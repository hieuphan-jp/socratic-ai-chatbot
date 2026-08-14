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

# JA: ★フリーチャット(knowledge_node未設定)が「完了」した際、会話内容から
#     知識ノードのtitle/contentをAIに要約させるための指示。
# VI: ★Chỉ thị để AI tóm tắt nội dung hội thoại thành title/content của
#     knowledge node, khi một phiên chat tự do (chưa gắn knowledge_node) "hoàn thành".
NODE_SUMMARY_SYSTEM_PROMPT = """
You are summarizing a tutoring conversation into a permanent study note for the student.

Based on the conversation so far, write a concise study note capturing what the student learned.

OUTPUT FORMAT (STRICT):
- Line 1: a short title (a few words, no trailing punctuation)
- From line 2 onward: a concise explanation of the concept, written for the student's own future review

Do not include any preamble, meta-commentary, or markdown formatting.
"""

NEEDS_AI_ANSWER = {"ANSWER", "REQUEST_CHANGE_METHOD"}
SESSION_NODE_TITLE_MAX_LEN = 255


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


def _summarize_session_as_node(session: ChatSession) -> tuple[str, str]:
    """
    JA: セッションの会話履歴全体をAIに渡し、知識ノードのtitle/contentを要約
        させる。1行目をtitle、2行目以降をcontentとして解釈する規約。
    VI: Đưa toàn bộ lịch sử hội thoại của session cho AI, nhờ tóm tắt thành
        title/content của knowledge node. Quy ước: dòng 1 là title, từ dòng
        2 trở đi là content.
    """
    llm = get_llm()
    history = [
        AIChatMessage(
            role="user" if msg.sender == ChatMessage.Sender.USER else "assistant",
            content=msg.message_text[:600],
        )
        for msg in session.messages.order_by("created_at")
    ]
    messages_payload = [
        AIChatMessage(role="system", content=NODE_SUMMARY_SYSTEM_PROMPT),
        *history,
        AIChatMessage(
            role="user",
            content="Summarize this conversation into a study note title and content now.",
        ),
    ]
    raw_response = llm.chat(messages_payload)
    if isinstance(raw_response, ChatResult):
        text = raw_response.text
    elif hasattr(raw_response, "text"):
        text = raw_response.text
    else:
        text = str(raw_response)
    text = text.strip()

    lines = text.splitlines()
    title = (lines[0].strip() if lines else "")[:SESSION_NODE_TITLE_MAX_LEN]
    content = "\n".join(lines[1:]).strip() or text
    return title or session.title, content


def create_knowledge_node_from_session(*, session: ChatSession, user, topic_id):
    """
    JA: フリーチャット(knowledge_node未設定)が「完了」した時に呼ばれる。
        会話内容からAIにtitle/contentを要約させ、指定Topic配下に新しい
        KnowledgeNodeとして保存し、このセッションと1:1(OneToOne)で紐付ける。
        KnowledgeNodeの作成自体は所有アプリ(apps.topics)のservices経由で行う
        (このアプリからKnowledgeNode.objects.createを直接呼ばない)。
    VI: Được gọi khi một phiên chat tự do (chưa gắn knowledge_node) "hoàn
        thành". Nhờ AI tóm tắt hội thoại thành title/content, lưu thành một
        KnowledgeNode mới dưới Topic được chỉ định, và gắn 1:1 (OneToOne)
        với session này. Việc tạo KnowledgeNode được ủy thác qua services
        của app sở hữu (apps.topics), không gọi thẳng
        KnowledgeNode.objects.create từ app này.
    """
    from apps.topics import services as topics_services

    topic = topics_services.get_owned_topic(user=user, topic_id=topic_id)
    title, content = _summarize_session_as_node(session)
    node = topics_services.create_knowledge_node(user=user, topic=topic, title=title, content=content)

    session.knowledge_node = node
    session.save(update_fields=["knowledge_node"])
    return node


def get_or_create_active_attempt(*, session: ChatSession) -> Attempt:
    attempt = session.attempts.filter(completed_at__isnull=True).order_by("-created_at").first()
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
    topic_id=None,
) -> dict:
    text = (user_message_text or "").strip()
    if action_type in NEEDS_AI_ANSWER and not text:
        raise ValidationError("メッセージ内容は必須です / Nội dung tin nhắn là bắt buộc")

    # JA: ★フリーチャット(knowledge_node未設定)がCOMPLETEした瞬間に、初めて
    #     知識ノードを作成しこのセッションと1:1で紐付ける。既にノードがある
    #     セッション(復習チャット)ではここは通らない。record_review_result は
    #     knowledge_node必須のため、この処理を先に済ませておく必要がある。
    # VI: ★Khi một phiên chat tự do (chưa gắn knowledge_node) COMPLETE lần
    #     đầu, tạo mới knowledge node và gắn 1:1 với session này. Session đã
    #     có sẵn node (chat ôn tập) sẽ không đi qua nhánh này. Vì
    #     record_review_result bắt buộc phải có knowledge_node, bước này cần
    #     làm trước.
    if action_type == "COMPLETE" and session.knowledge_node_id is None:
        if not topic_id:
            raise ValidationError(
                "知識ノードとして保存するTopicを選択してください / Vui lòng chọn Topic để lưu"
            )
        create_knowledge_node_from_session(session=session, user=session.user, topic_id=topic_id)

    if action_type in ("HINT", "COMPLETE"):
        record_hint_or_completion(session=session, action_type=action_type, understood=understood)

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
