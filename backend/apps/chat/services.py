# JA: Chat機能と ReviewLog / KnowledgeNode の連携ロジック + AI応答生成・分岐推定・会話履歴
# VI: Logic kết nối giữa Chat, ReviewLog, KnowledgeNode + sinh câu trả lời AI, đoán nhánh, nhớ lịch sử hội thoại
import json
import logging
import re
from typing import Any, Dict

from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.ai.base import ChatMessage as AIChatMessage, ChatResult

from apps.ai.base import ChatMessage as AIChatMessage
from apps.ai.base import ChatResult
from apps.ai.client import get_llm
from apps.reviews.models import ReviewLog
from apps.topics.models import KnowledgeNode

from .models import ChatMessage, ChatSession

logger = logging.getLogger(__name__)

# JA: ★家庭教師としての役割をより明確に指示。ヒントを段階的に導き、直接の答えは出さない。
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

# JA: 分岐推定およびAI Tutor用のシステムプロンプト定義（Option 1）
# VI: Định nghĩa system prompt cho AI Tutor và đoán nhánh tư duy (Option 1)
BRANCHING_SYSTEM_PROMPT = """
あなたは学習者を指導する AI Tutor です。
ユーザーの質問に対してヒントを提供すると同時に、思考ツリーの分岐先（親ノード）を正確に推定してください。

【重要：分岐判定ガイドライン / Quy tắc phát hiện rẽ nhánh】
ユーザーの最新の質問について、以下の条件をチェックしてください：
1. **話題の切り替え・復帰**: ユーザーが直前の会話（N-1）を連続して深掘りせず、過去の質問（N-2, N-3...）の話題に戻っているか？
2. **参照単語の検知**: 「さっきの〜」「最初の〜」「〜についてだけど」「chủ đề trước...」「câu đầu tiên...」「nãy bạn nói...」などの過去を参照するキーワードが含まれているか？
3. **文脈の断絶**: 直前の会話と最新の質問のトピックが完全に切れているか？

【出力フォーマット / Format đầu ra】
必ず以下の JSON フォーマットのみで返答してください。余計なテキストや Markdown コードブロックを含めないでください。

{
  "answer": "ユーザーへのヒント回答 / Lời thoại trả lời cho User",
  "suggested_parent_id": "最も関連性の高い過去の USER メッセージの UUID (分岐がない場合は null) / UUID của câu hỏi USER tương ứng trong quá khứ nếu rẽ nhánh, ngược lại là null",
  "confidence": "high | medium | low"
}
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


def _build_branching_instructions(user_nodes: list, text: str) -> str:
    """
    JA: ノードインデックス形式で過去の質問履歴を整形（Option 2）。
        直前のノードではなく、過去の古いノードへの分岐のみを明確に検出させる。
    VI: Format lịch sử câu hỏi USER theo dạng Node Index kèm UUID (Option 2).
        Chỉ thị AI nhận biết khi user quay lại rẽ nhánh từ một node cũ hơn node ngay liền trước.
    """
    history_formatted = []
    for idx, msg in enumerate(user_nodes, start=1):
        history_formatted.append(f"- [Node ID: {msg.id}] (Bước {idx}): {msg.message_text[:NODE_TOPIC_MAX_LEN]}")

    history_str = "\n".join(history_formatted) if history_formatted else "Không có câu hỏi cũ nào."

    return f"""
{BRANCHING_SYSTEM_PROMPT}

=== LỊCH SỬ CÁC CÂU HỎI TRƯỚC ĐÂY CỦA USER (TỪ CŨ ĐẾN MỚI) ===
{history_str}

=== CÂU HỎI MỚI NHẤT CỦA USER ===
"{text}"

=== YÊU CẦU / INSTRUCTIONS ===
1. So sánh CÂU HỎI MỚI NHẤT với LỊCH SỬ CÁC CÂU HỎI TRƯỚC ĐÂY.
2. Nếu CÂU HỎI MỚI NHẤT đang muốn hỏi nối tiếp hoặc rẽ nhánh từ một [Node ID] cũ hơn (từ Bước 1 đến Bước N-2) thay vì câu liền trước (Bước N-1), hãy gán chuỗi UUID của [Node ID] đó vào `suggested_parent_id` và đặt `confidence` thành "high".
3. Nếu chỉ là câu hỏi tiếp nối tự nhiên của câu liền trước (Bước N-1), hãy gán `suggested_parent_id` là null và `confidence` là "low".
4. Trả về đúng định dạng JSON yêu cầu.
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

    # Build prompt đoán nhánh nâng cao (Option 1 + Option 2)
    branching_instructions = _build_branching_instructions(user_nodes, text)
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
            if suggested_id and str(suggested_id).lower() != "null":
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
    """
    JA: ユーザーが分岐先（親ノード）を確定または thay đổi するロジック。
        parent_message_id と parent_message_id (DBカラム) の両方を確実に更新・保存する。
    VI: Logic user xác nhận hoặc đổi node cha (rẽ nhánh).
        Đảm bảo cập nhật và lưu cả mối quan hệ parent_message lẫn cột parent_message_id dưới DB.
    """
    # JA: 対象のユーザーメッセージを取得 / VI: Lấy tin nhắn của USER cần xác nhận
    message = ChatMessage.objects.filter(
        session=session, id=message_id, sender=ChatMessage.Sender.USER
    ).first()
    
    if message is None:
        raise ValidationError("メッセージが見つかりません / Không tìm thấy tin nhắn")

    # JA: parent_message_id が dict 型で渡された場合の bóc tách 処理 / VI: Xử lý bóc tách nếu truyền nhầm dạng Dict/Object
    actual_parent_id = parent_message_id
    if isinstance(parent_message_id, dict):
        actual_parent_id = parent_message_id.get("id")

    parent = None
    if actual_parent_id:
        parent = ChatMessage.objects.filter(session=session, id=actual_parent_id).first()
        if parent is None:
            raise ValidationError("親メッセージが見つかりません / Không tìm thấy tin nhắn cha")

    # JA: 親ノードの更新と確認フラグの設定 / VI: Cập nhật node cha và đánh dấu đã confirm
    message.parent_message = parent
    message.parent_confirmed = True
    
    # JA: ★重要：DBの parent_message_id カラムを確実に保存するために update_fields に chỉ định する
    # VI: ★Quan trọng: Chỉ định rõ parent_message_id trong update_fields để ghi nhận xuống DB ngay lập tức
    message.save(update_fields=["parent_message", "parent_message_id", "parent_confirmed"])
    
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
