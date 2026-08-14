# JA: Chat機能の純粋な業務ロジック（HTTP非依存）
import logging

from django.utils import timezone

from apps.ai.base import ChatMessage as AIChatMessage
from apps.ai.base import ChatResult
from apps.ai.client import get_llm
from apps.common.exceptions import ValidationError

from .models import Attempt, ChatMessage, ChatSession

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
You are an AI Tutor. Guide the user step by step through learning.
NEVER give direct full answers. Provide hint-based guidance and review answers.
"""

NEEDS_AI_ANSWER = {"ANSWER", "REQUEST_CHANGE_METHOD"}


def create_chat_session_for_node(*, user, node_id=None, title: str = "New Session") -> ChatSession:
    from apps.topics.models import KnowledgeNode

    node = None
    if node_id:
        node = KnowledgeNode.objects.filter(id=node_id).first()
        if not node:
            raise ValidationError("KnowledgeNodeが見つかりません / Không tìm thấy KnowledgeNode")

        existing = ChatSession.objects.filter(knowledge_node=node, user=user).first()
        if existing:
            return existing

        if title == "New Session":
            title = f"学習: {node.title}"

    return ChatSession.objects.create(user=user, knowledge_node=node, title=title)


def get_or_create_active_attempt(*, session: ChatSession) -> Attempt:
    attempt = (
        session.attempts.filter(completed_at__isnull=True).order_by("-created_at").first()
    )
    if attempt is None:
        attempt = Attempt.objects.create(chat_session=session)
    return attempt


def record_hint_or_completion(
    *, session: ChatSession, action_type: str, understood: bool | None = None
):
    attempt = get_or_create_active_attempt(session=session)

    if action_type == "HINT":
        attempt.hint_count += 1
        attempt.save(update_fields=["hint_count"])

    if action_type == "COMPLETE":
        attempt.completed_at = timezone.now()
        attempt.save(update_fields=["completed_at"])

        from apps.reviews.services import record_review_result

        record_review_result(attempt, bool(understood))

    return attempt


def get_session_graph_data(*, session: ChatSession) -> dict:
    messages = session.messages.all().order_by("created_at")

    nodes = []
    edges = []

    for msg in messages:
        nodes.append(
            {
                "id": str(msg.id),
                "type": "stepNode" if msg.node_type == "STEP" else "answerNode",
                "data": {
                    "label": msg.sender,
                    "text": msg.message_text,
                    "node_type": msg.node_type,
                },
            }
        )

        if msg.parent_message_id:
            edges.append(
                {
                    "id": f"e-{msg.parent_message_id}-{msg.id}",
                    "source": str(msg.parent_message_id),
                    "target": str(msg.id),
                }
            )

    return {"nodes": nodes, "edges": edges}


def send_message_and_get_ai_response(
    *,
    session: ChatSession,
    user_message_text: str,
    parent_message_id=None,
    action_type: str = "ANSWER",
    understood: bool | None = None,
) -> dict:
    text = (user_message_text or "").strip()
    if action_type in NEEDS_AI_ANSWER and not text:
        raise ValidationError("メッセージ内容は必須です / Nội dung tin nhắn là bắt buộc")

    if action_type in ("HINT", "COMPLETE"):
        record_hint_or_completion(
            session=session, action_type=action_type, understood=understood
        )

    parent_msg = None
    if parent_message_id:
        parent_msg = ChatMessage.objects.filter(session=session, id=parent_message_id).first()

    user_node_type = (
        ChatMessage.NodeType.ANSWER
        if action_type == "ANSWER"
        else ChatMessage.NodeType.CHANGE_METHOD
    )
    user_msg = None
    if text:
        user_msg = ChatMessage.objects.create(
            session=session,
            parent_message=parent_msg,
            sender=ChatMessage.Sender.USER,
            message_text=text,
            node_type=user_node_type,
        )

    if action_type == "HINT":
        ai_text = "続けてみましょう。分からない部分をもう少し詳しく教えてください。"
    elif action_type == "COMPLETE":
        ai_text = "お疲れ様でした！学習の記録を保存しました。"
    else:
        llm = get_llm()

        messages_payload = [
            AIChatMessage(role="system", content=SYSTEM_PROMPT),
            AIChatMessage(role="user", content=f"Action: {action_type}\nMessage: {text}"),
        ]

        try:
            raw_response = llm.chat(messages_payload)

            if isinstance(raw_response, ChatResult):
                ai_text = raw_response.text
            elif hasattr(raw_response, "text"):
                ai_text = raw_response.text
            else:
                ai_text = str(raw_response)

        except Exception as e:
            logger.error("JA: AI応答生成エラー: %s / VI: Lỗi tạo phản hồi AI: %s", e, e)
            ai_text = f"[AI Tutor] Lỗi tạo phản hồi từ AI: {str(e)}"

    ai_msg = ChatMessage.objects.create(
        session=session,
        parent_message=user_msg,
        sender=ChatMessage.Sender.AI,
        message_text=str(ai_text),
        node_type=ChatMessage.NodeType.STEP,
        is_hint=(action_type == "HINT"),
    )

    return {"user_message": user_msg, "ai_message": ai_msg}