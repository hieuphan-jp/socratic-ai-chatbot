# JA: Chat機能と ReviewLog / KnowledgeNode の連携ロジック + AI応答生成・分岐推定・会話履歴
# VI: Logic kết nối giữa Chat, ReviewLog, KnowledgeNode + sinh câu trả lời AI, đoán nhánh, nhớ lịch sử hội thoại
import json
import logging
import re
from typing import Any, Dict

from django.utils import timezone

from apps.ai.base import ChatMessage as AIChatMessage, ChatResult

from apps.ai.base import ChatMessage as AIChatMessage
from apps.ai.base import ChatResult
from apps.ai.client import get_llm
from apps.common.exceptions import ValidationError
from apps.reviews.models import ReviewLog
from apps.topics.models import KnowledgeNode

from .models import ChatMessage, ChatSession

logger = logging.getLogger(__name__)

# JA: ★家庭教師としての役割をより明確に指示。ヒント段階的に導き、直接の答えは出さない。
# VI: ★Chỉ thị rõ ràng hơn vai trò gia sư. Dẫn dắt bằng gợi ý từng bước, không đưa thẳng đáp án.
SYSTEM_PROMPT = """
You are an AI Tutor helping a student learn step by step.

STRICT RULES:
1. NEVER give the complete/final answer directly, even if the user asks for it directly or insists.
2. Instead, guide with a hint, a leading question, or reveal only a small piece of the concept at a time.
3. If the user's attempt is close to correct, confirm what's right and encourage them to continue, without revealing the rest.
4. If the user seems stuck, break the problem into a smaller, easier sub-question rather than solving it for them.
5. You have access to the full conversation history below (previous questions and your previous replies).
   Use it to stay consistent and to correctly recall anything the user or you mentioned earlier.
6. Keep responses concise (a few sentences), conversational, and encouraging.
"""

NEEDS_AI_ANSWER = {"ANSWER", "REQUEST_CHANGE_METHOD"}
NODE_TOPIC_MAX_LEN = 100

MAX_HISTORY_MESSAGES = 20
HISTORY_MESSAGE_MAX_LEN = 600


def create_chat_session_for_node(*, user, node_id: int = None, title: str = "New Study Session") -> ChatSession:
    """
    JA: 指定された KnowledgeNode に基づいて ChatSession (Attempt) を作成
    VI: Tạo ChatSession (Attempt) mới dựa trên KnowledgeNode được chỉ định
    """
    node = None
    if node_id:
        node = KnowledgeNode.objects.filter(id=node_id).first()
        if not node:
            raise ValidationError("Knowledge Node không tồn tại.")
        if title in ["New Study Session", "New Chat Session"]:
            title = f"Học: {node.title}"

    session = ChatSession.objects.create(
        user=user,
        knowledge_node=node,
        title=title,
        hint_count=0,
    )
    return session


def record_hint_or_completion(*, session: ChatSession, action_type: str, response_time_seconds: int = 60):
    """
    JA: ヒントカウントの更新および学習完了時 (COMPLETE) の ReviewLog 作成
    VI: Cập nhật hint_count và tự động tạo ReviewLog khi hoàn thành (COMPLETE)
    """
    if action_type == "HINT":
        session.hint_count += 1
        session.save(update_fields=["hint_count"])

    if action_type == "COMPLETE":
        session.completed_at = timezone.now()
        session.save(update_fields=["completed_at"])

        if session.hint_count == 0:
            rating = 5
        elif session.hint_count == 1:
            rating = 4
        elif session.hint_count == 2:
            rating = 3
        elif session.hint_count == 3:
            rating = 2
        elif session.hint_count == 4:
            rating = 1
        else:
            rating = 0

        review_log = ReviewLog.objects.create(
            attempt=session,
            performance_rating=rating,
            response_time_seconds=response_time_seconds,
        )
        logger.info("JA: ReviewLog を作成しました (Rating: %s) / VI: Đã tạo ReviewLog (Rating: %s)", rating, rating)
        return review_log

    return None


def _extract_text(raw_response) -> str:
    if isinstance(raw_response, ChatResult):
        return raw_response.text
    if hasattr(raw_response, "text"):
        return raw_response.text
    return str(raw_response)


def _extract_json(raw_text: str) -> dict | None:
    try:
        return json.loads(raw_text)
    except (json.JSONDecodeError, TypeError):
        pass

    match = re.search(r"\{.*\}", raw_text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return None
    return None


def _build_node_summaries(session: ChatSession) -> list[dict]:
    """
    JA: 全メッセージ（User/AI）を対象に分岐推定用の要約リストを作成する。
    VI: Lấy tất cả tin nhắn trong phiên (cả User và AI) để AI có thể rẽ nhánh từ câu hỏi/câu trả lời bất kỳ.
    """
    all_msgs = (
        session.messages.all()
        .order_by("created_at")[:15]  # Lấy tối đa 15 node gần nhất để tiết kiệm token
    )
    summaries = []
    for msg in all_msgs:
        sender_label = "User" if msg.sender == ChatMessage.Sender.USER else "AI"
        summaries.append({
            "id": str(msg.id),
            "sender": sender_label,
            "text": msg.message_text[:NODE_TOPIC_MAX_LEN]
        })
    return summaries


def _build_history_messages(session: ChatSession) -> list[AIChatMessage]:
    """
    JA: これまでの会話履歴を AIChatMessage のリストに変換し、AI に渡す。
    VI: Chuyển lịch sử hội thoại đã có thành danh sách AIChatMessage để đưa cho AI.
    """
    past_messages = session.messages.order_by("-created_at")[:MAX_HISTORY_MESSAGES]
    history = []
    for msg in reversed(list(past_messages)):
        role = "user" if msg.sender == ChatMessage.Sender.USER else "assistant"
        content = msg.message_text[:HISTORY_MESSAGE_MAX_LEN]
        history.append(AIChatMessage(role=role, content=content))
    return history

def _build_branching_instructions(node_summaries: list[dict], action_type: str, text: str) -> str:
    """
    JA: 分岐推定の指示文（直前のノードではなく、過去の古いノードへの分岐のみを検出）
    VI: Chỉ thị đoán nhánh (Chỉ phát hiện khi user quay lại rẽ nhánh từ một node cũ hơn node ngay trước đó)
    """
    steps_json = json.dumps(node_summaries, ensure_ascii=False)
    return f"""
LIST OF PREVIOUS USER QUESTIONS (id and text):
{steps_json}

NEW USER QUESTION: "{text}"

TASK: Analyze if the NEW USER QUESTION is asking about or continuing an OLDER topic from the list above (instead of the most recent question).
- If the new question clearly branches off an OLDER question from the list, set "suggested_parent_id" to that older question's id, and set "confidence" to "high".
- If it is just a natural continuation of the MOST RECENT question, set "suggested_parent_id" to null and "confidence" to "low".

OUTPUT FORMAT (STRICT JSON ONLY, NO MARKDOWN, NO EXTRA TEXT):
{{"suggested_parent_id": "<id_of_older_question_or_null>", "confidence": "high_or_low", "answer": "<your tutor response to the student>"}}
"""


def _generate_ai_answer(*, session: ChatSession, explicit_parent, action_type: str, text: str):
    llm = get_llm()
    history = _build_history_messages(session)

    # Lấy tất cả các câu hỏi cũ của USER trong session
    user_nodes = list(
        session.messages.filter(sender=ChatMessage.Sender.USER)
        .order_by("created_at")
    )

    # NẾU MỚI CHỈ CÓ 0 HOẶC 1 CÂU HỎI USER: Không cần đoán nhánh (tránh hiện Confirm thừa ở câu đầu)
    if explicit_parent is not None or len(user_nodes) <= 1:
        messages_payload = [
            AIChatMessage(role="system", content=SYSTEM_PROMPT),
            *history,
            AIChatMessage(role="user", content=f"Action: {action_type}\nMessage: {text}"),
        ]
        try:
            raw_response = llm.chat(messages_payload)
            return _extract_text(raw_response), None, "", True
        except Exception as e:
            logger.error("Lỗi tạo phản hồi AI: %s", e)
            return f"[AI Tutor] Lỗi: {str(e)}", None, "", True

    # Tạo danh sách các câu hỏi cũ để AI so sánh rẽ nhánh
    node_summaries = [
        {"id": str(msg.id), "text": msg.message_text[:NODE_TOPIC_MAX_LEN]}
        for msg in user_nodes
    ]

    branching_instructions = _build_branching_instructions(node_summaries, action_type, text)
    messages_payload = [
        AIChatMessage(role="system", content=SYSTEM_PROMPT),
        *history,
        AIChatMessage(role="user", content=branching_instructions),
    ]

    try:
        raw_response = llm.chat(messages_payload)
        raw_text = _extract_text(raw_response)
        parsed = _extract_json(raw_text)

        if parsed and isinstance(parsed, dict) and "answer" in parsed:
            ai_text = parsed["answer"]
            parent_confidence = parsed.get("confidence", "low") or "low"
            suggested_parent = None
            suggested_id = parsed.get("suggested_parent_id")

            # Chỉ chấp nhận suggested_parent nếu ID đó thực sự tồn tại trong DB
            if suggested_id and suggested_id != "null":
                suggested_parent = ChatMessage.objects.filter(session=session, id=suggested_id).first()

            # Nếu AI tự tin rẽ nhánh về câu cũ (confidence == "high"), đặt parent_confirmed = False để hiện Confirm
            parent_confirmed = False if (parent_confidence == "high" and suggested_parent) else True
            return ai_text, suggested_parent, parent_confidence, parent_confirmed

        # Fallback nếu AI trả về văn bản thường thay vì JSON
        return raw_text, None, "", True
    except Exception as e:
        logger.error("Lỗi tạo phản hồi AI: %s", e)
        return f"[AI Tutor] Lỗi: {str(e)}", None, "", True

def send_message_and_get_ai_response(
    *,
    session: ChatSession,
    user_message_text: str = "",
    parent_message_id: str = None,
    action_type: str = "ANSWER",
) -> Dict[str, Any]:
    text = (user_message_text or "").strip()

    if action_type in NEEDS_AI_ANSWER and not text:
        raise ValidationError("メッセージ内容は必須です / Nội dung tin nhắn là bắt buộc")

    if action_type in ["HINT", "COMPLETE"]:
        record_hint_or_completion(session=session, action_type=action_type)

    explicit_parent = None
    if parent_message_id:
        explicit_parent = ChatMessage.objects.filter(id=parent_message_id, session=session).first()

    suggested_parent = None
    parent_confidence = ""
    parent_confirmed = True

    if action_type == "HINT":
        ai_text = f"Gợi ý #{session.hint_count}: Hãy tập trung vào định nghĩa cốt lõi của bài học."
    elif action_type == "COMPLETE":
        ai_text = "Bài học đã hoàn thành! Hệ thống đã tự động lưu kết quả ôn tập vào lịch sử của bạn."
    else:
        ai_text, suggested_parent, parent_confidence, parent_confirmed = _generate_ai_answer(
            session=session, explicit_parent=explicit_parent, action_type=action_type, text=text
        )

    # Chọn final_parent cho user_message
    final_parent = explicit_parent or suggested_parent
    if final_parent is None:
        final_parent = session.messages.order_by("-created_at").first()

    user_message = None
    if text or action_type != "ANSWER":
        is_hint_flag = action_type == "HINT"
        text_to_save = text if text else f"[{action_type}] Request"
        user_node_type = (
            ChatMessage.NodeType.CHANGE_METHOD
            if action_type == "REQUEST_CHANGE_METHOD"
            else ChatMessage.NodeType.ANSWER
        )
        user_message = ChatMessage.objects.create(
            session=session,
            parent_message=final_parent,
            suggested_parent=suggested_parent,
            parent_confidence=parent_confidence,
            parent_confirmed=parent_confirmed,
            sender=ChatMessage.Sender.USER,
            message_text=text_to_save,
            is_hint=is_hint_flag,
            node_type=user_node_type,
        )

    ai_message = ChatMessage.objects.create(
        session=session,
        parent_message=user_message if user_message else explicit_parent,
        sender=ChatMessage.Sender.AI,
        message_text=ai_text,
        is_hint=(action_type == "HINT"),
        node_type=ChatMessage.NodeType.STEP,
    )

    return {"user_message": user_message, "ai_message": ai_message}


def confirm_message_parent(*, session: ChatSession, message_id, parent_message_id) -> ChatMessage:
    message = ChatMessage.objects.filter(
        session=session, id=message_id, sender=ChatMessage.Sender.USER
    ).first()
    
    if message is None:
        raise ValidationError("メッセージが見つかりません / Không tìm thấy tin nhắn")

    parent = None
    if parent_message_id:
        parent = ChatMessage.objects.filter(session=session, id=parent_message_id).first()
        if parent is None:
            raise ValidationError("親メッセージが見つかりません / Không tìm thấy tin nhắn cha")

    # VI: Cập nhật parent_message mới, đánh dấu đã confirm và lưu DB
    message.parent_message = parent
    message.parent_confirmed = True
    message.save(update_fields=["parent_message", "parent_confirmed"])
    
    return message


def get_session_graph_data(*, session: ChatSession) -> Dict[str, Any]:
    messages = session.messages.all().order_by("created_at")
    nodes = []
    edges = []

    for msg in messages:
        nodes.append(
            {
                "id": str(msg.id),
                "sender": msg.sender,
                "text": msg.message_text,
                "is_hint": msg.is_hint,
                "node_type": msg.node_type,
                "created_at": msg.created_at.isoformat(),
                "parent_confirmed": msg.parent_confirmed,
                "parent_confidence": msg.parent_confidence,
                "suggested_parent_id": str(msg.suggested_parent_id) if msg.suggested_parent_id else None,
            }
        )
        if msg.parent_message_id:
            edges.append({"source": str(msg.parent_message_id), "target": str(msg.id)})

    return {"session_id": str(session.id), "nodes": nodes, "edges": edges}
