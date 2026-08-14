# JA: Chat機能の純粋な業務ロジック（HTTP非依存）
#     【設計変更2026-08-13】create_chat_session を
#     create_chat_session_for_node に置き換え(既存セッションの再利用に
#     対応)。hint_count・completed_atはChatSessionからAttemptへ移動した
#     ため、get_or_create_active_attempt・record_hint_or_completionを
#     新設。send_message_and_get_ai_responseはHINT/COMPLETEアクションを
#     処理できるようにした(AIを呼ばず、Attemptの更新のみ行う)。
# VI: Logic nghiệp vụ thuần túy của tính năng Chat (không phụ thuộc HTTP).
#     【Thay đổi thiết kế 2026-08-13】Thay create_chat_session bằng
#     create_chat_session_for_node (hỗ trợ tái sử dụng session hiện có).
#     hint_count/completed_at đã chuyển từ ChatSession sang Attempt nên
#     thêm mới get_or_create_active_attempt/record_hint_or_completion.
#     send_message_and_get_ai_response giờ xử lý được action HINT/COMPLETE
#     (không gọi AI, chỉ cập nhật Attempt).
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

# JA: ANSWER・REQUEST_CHANGE_METHODだけがAI応答を必要とする
#     (HINT・COMPLETEはAttemptの更新のみで、AIは呼ばない)
# VI: Chỉ ANSWER/REQUEST_CHANGE_METHOD mới cần AI trả lời (HINT/COMPLETE
#     chỉ cập nhật Attempt, không gọi AI)
NEEDS_AI_ANSWER = {"ANSWER", "REQUEST_CHANGE_METHOD"}


def create_chat_session_for_node(*, user, node_id=None, title: str = "New Session") -> ChatSession:
    """
    JA: 指定されたKnowledgeNodeに基づいてChatSessionを取得する。
        knowledge_nodeはOneToOneFieldなので、すでにそのノード向けの
        セッションが存在すればそれを返し、無ければ新規作成する
        (「同じノードなら常に同じ永続チャットに戻る」ため)。
    VI: Lấy ChatSession dựa trên KnowledgeNode. Vì knowledge_node là
        OneToOneField, nếu đã có session cho node này thì trả về, chưa có
        thì tạo mới (để "cùng 1 node luôn quay lại đúng 1 chat cố định").
    """
    from apps.topics.models import KnowledgeNode  # アプリ間の循環importを避けるため関数内import

    node = None
    if node_id:
        node = KnowledgeNode.objects.filter(id=node_id).first()
        if not node:
            raise ValidationError("KnowledgeNodeが見つかりません / Không tìm thấy KnowledgeNode")

        # JA: すでにこのノード向けのセッションがあれば再利用する
        # VI: Nếu đã có session cho node này thì dùng lại
        existing = ChatSession.objects.filter(knowledge_node=node, user=user).first()
        if existing:
            return existing

        if title == "New Session":
            title = f"学習: {node.title}"

    return ChatSession.objects.create(user=user, knowledge_node=node, title=title)


def get_or_create_active_attempt(*, session: ChatSession) -> Attempt:
    """
    JA: 現在進行中(completed_at未設定)のAttemptを返す。無ければ新規作成する。
        前回のAttemptがすでに完了しているなら、新しい回として新規作成する。
        これが「何回目の復習か」の区切りになる。
    VI: Trả về Attempt đang thực hiện (chưa có completed_at). Nếu không có
        thì tạo mới. Nếu Attempt trước đã hoàn thành thì tạo mới cho lần
        này. Đây là ranh giới "lần ôn tập thứ mấy".
    """
    attempt = (
        session.attempts.filter(completed_at__isnull=True).order_by("-created_at").first()
    )
    if attempt is None:
        attempt = Attempt.objects.create(chat_session=session)
    return attempt


def record_hint_or_completion(
    *, session: ChatSession, action_type: str, understood: bool | None = None
):
    """
    JA: ヒントカウントの更新(該当するAttemptに対して)、および学習完了時
        (COMPLETE)の間隔復習機能への引き継ぎ。ReviewLog作成・SM-2計算は
        apps.reviews側の責務なので、ここではその呼び出しだけを行う。
    VI: Cập nhật hint_count (trên Attempt tương ứng), và bàn giao cho tính
        năng ôn tập ngắt quãng khi hoàn thành (COMPLETE). Tạo ReviewLog và
        tính SM-2 là trách nhiệm của apps.reviews, ở đây chỉ gọi hàm đó.
    """
    attempt = get_or_create_active_attempt(session=session)

    if action_type == "HINT":
        attempt.hint_count += 1
        attempt.save(update_fields=["hint_count"])

    if action_type == "COMPLETE":
        attempt.completed_at = timezone.now()
        attempt.save(update_fields=["completed_at"])

        # JA: アプリ間の循環importを避けるため関数内import
        # VI: Import trong hàm để tránh circular import giữa các app
        from apps.reviews.services import record_review_result

        record_review_result(attempt, bool(understood))

    return attempt


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
    understood: bool | None = None,
) -> dict:
    """JA: ユーザーメッセージを保存し、AI応答を生成(HINT/COMPLETEはAIを呼ばない)
    VI: Lưu tin nhắn user và tạo phản hồi AI (HINT/COMPLETE không gọi AI)
    """
    text = (user_message_text or "").strip()
    if action_type in NEEDS_AI_ANSWER and not text:
        raise ValidationError("メッセージ内容は必須です / Nội dung tin nhắn là bắt buộc")

    # JA: HINT・COMPLETEはAttemptの更新(ヒントカウント・完了報告)を行う。
    #     COMPLETEの場合はここで間隔復習機能(apps.reviews)のSM-2計算まで
    #     連動する。
    # VI: HINT/COMPLETE cập nhật Attempt (đếm gợi ý, báo hoàn thành). Với
    #     COMPLETE sẽ liên động tới tính SM-2 ở tính năng ôn tập
    #     (apps.reviews) luôn tại đây.
    if action_type in ("HINT", "COMPLETE"):
        record_hint_or_completion(
            session=session, action_type=action_type, understood=understood
        )

    # 1. Tìm parent message nếu có
    parent_msg = None
    if parent_message_id:
        parent_msg = ChatMessage.objects.filter(session=session, id=parent_message_id).first()

    # 2. Lưu tin nhắn User (nếu có nội dung; HINT/COMPLETE có thể không có text)
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

    # 3. HINT/COMPLETEは定型応答、それ以外はAIを呼ぶ
    if action_type == "HINT":
        ai_text = "続けてみましょう。分からない部分をもう少し詳しく教えてください。"
    elif action_type == "COMPLETE":
        ai_text = "お疲れ様でした！学習の記録を保存しました。"
    else:
        # Lấy LLM provider và tạo phản hồi
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

    # 4. Lưu tin nhắn AI (là con của user_msg nếu có)
    ai_msg = ChatMessage.objects.create(
        session=session,
        parent_message=user_msg,
        sender=ChatMessage.Sender.AI,
        message_text=str(ai_text),
        node_type=ChatMessage.NodeType.STEP,
        is_hint=(action_type == "HINT"),
    )

    return {"user_message": user_msg, "ai_message": ai_msg}