# JA: Chat機能の純粋な業務ロジック（HTTP非依存） / VI: Logic nghiệp vụ thuần túy của tính năng Chat (không phụ thuộc HTTP)
import logging

from apps.ai.base import ChatMessage as AIChatMessage
from apps.ai.base import ChatResult
from apps.ai.client import get_llm
from apps.common.exceptions import ValidationError

from .models import ChatMessage, ChatSession

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
You are an AI Tutor. Guide the user step by step through learning.
NEVER give direct full answers. Provide hint-based guidance and review answers.
"""


def create_chat_session(*, user, title: str = "New Session") -> ChatSession:
    """JA: 新しいチャットセッションを作成 / VI: Tạo phiên chat mới"""
    return ChatSession.objects.create(user=user, title=title)


def get_session_graph_data(*, session: ChatSession) -> dict:
    """JA: チャット履歴を React Flow の Nodes/Edges 構造に変換 / VI: Chuyển đổi lịch sử chat sang cấu trúc Nodes/Edges của React Flow"""
    messages = session.messages.all().order_by("created_at")

    nodes = []
    edges = []

    for msg in messages:
        # Tạo Node
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

        # Tạo Edge (nối từ parent_message tới msg hiện tại)
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
) -> dict:
    """JA: ユーザーメッセージを保存し、AI応答を生成 / VI: Lưu tin nhắn user và tạo phản hồi AI"""
    text = (user_message_text or "").strip()
    if not text:
        raise ValidationError("メッセージ内容は必須です / Nội dung tin nhắn là bắt buộc")

    # 1. Tìm parent message nếu có
    parent_msg = None
    if parent_message_id:
        parent_msg = ChatMessage.objects.filter(session=session, id=parent_message_id).first()

    # 2. Lưu tin nhắn User
    user_node_type = (
        ChatMessage.NodeType.ANSWER
        if action_type == "ANSWER"
        else ChatMessage.NodeType.CHANGE_METHOD
    )
    user_msg = ChatMessage.objects.create(
        session=session,
        parent_message=parent_msg,
        sender=ChatMessage.Sender.USER,
        message_text=text,
        node_type=user_node_type,
    )

    # 3. Lấy LLM provider và tạo phản hồi
    llm = get_llm()

    # JA: base.py の ChatMessage スキーマに準拠したペイロードを構築
    # VI: Dùng đúng cấu trúc AIChatMessage chuẩn của hợp đồng base.py
    messages_payload = [
        AIChatMessage(role="system", content=SYSTEM_PROMPT),
        AIChatMessage(role="user", content=f"Action: {action_type}\nMessage: {text}"),
    ]

    try:
        raw_response = llm.chat(messages_payload)

        # JA: ChatResult オブジェクトからテキストを抽出
        # VI: Bóc tách lấy text thuần túy từ đối tượng ChatResult
        if isinstance(raw_response, ChatResult):
            ai_text = raw_response.text
        elif hasattr(raw_response, "text"):
            ai_text = raw_response.text
        else:
            ai_text = str(raw_response)

    except Exception as e:
        logger.error("JA: AI応答生成エラー: %s / VI: Lỗi tạo phản hồi AI: %s", e, e)
        ai_text = f"[AI Tutor] Lỗi tạo phản hồi từ AI: {str(e)}"

    # 4. Lưu tin nhắn AI (là con của user_msg)
    ai_msg = ChatMessage.objects.create(
        session=session,
        parent_message=user_msg,
        sender=ChatMessage.Sender.AI,
        message_text=str(ai_text),
        node_type=ChatMessage.NodeType.STEP,
    )

    return {"user_message": user_msg, "ai_message": ai_msg}
