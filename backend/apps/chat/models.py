# JA: Chat機能のモデル定義。
#     【設計変更 2026-08-13】ChatSession.knowledge_node を OneToOneField 化
#     (1ノードにつき常に1セッション)。hint_count・completed_at は
#     ChatSessionではなく新設のAttempt(1セッションにつきN件、「何回目の
#     復習か」を区別する)に移した。
# VI: Định nghĩa model tính năng Chat.
#     【Thay đổi thiết kế 2026-08-13】Chuyển ChatSession.knowledge_node
#     thành OneToOneField (1 node luôn ứng với 1 session). hint_count/
#     completed_at chuyển từ ChatSession sang Attempt mới thêm (1 session
#     ứng với N Attempt, để phân biệt "lần ôn tập thứ mấy").
from django.conf import settings
from django.db import models

from apps.common.models import BaseModel  # UUID PK + timestamps
from apps.topics.models import KnowledgeNode


class ChatSession(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chat_sessions",
    )
    title = models.CharField(max_length=255, default="New Chat Session")

    knowledge_node = models.OneToOneField(
        KnowledgeNode,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="chat_session",
    )

    def __str__(self) -> str:
        return f"{self.user.username} - {self.title}"


class Attempt(BaseModel):
    chat_session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name="attempts")
    hint_count = models.PositiveIntegerField(default=0, help_text="ヒントを求めた回数")
    completed_at = models.DateTimeField(null=True, blank=True, help_text="完了した日時")

    class Meta:
        ordering = ["-created_at"]
        # JA: 【設計変更 2026-08-17】1セッションにつき「未完了のAttempt」は同時に
        #     1件までに制限する部分ユニーク制約。完了ボタンの二重押下(ほぼ同時に
        #     2リクエストが飛ぶ)で、どちらも「未完了のAttemptが無い」と判定して
        #     Attemptを2件作ってしまい、SM-2の復習記録が二重に適用される不具合が
        #     あった。DBレベルで弾くことで、アプリ側のタイミングに関係なく防ぐ
        #     (services.get_or_create_active_attemptがIntegrityErrorを拾って
        #     既存の1件に合流する)。
        # VI: 【Thay đổi thiết kế 2026-08-17】Ràng buộc unique một phần: mỗi session
        #     chỉ được có tối đa 1 Attempt "chưa hoàn thành" tại một thời điểm.
        #     Bấm nút hoàn thành 2 lần liên tiếp (gần như đồng thời) khiến cả 2
        #     request đều thấy "chưa có Attempt đang mở" nên tạo ra 2 Attempt,
        #     làm SM-2 ghi nhận ôn tập bị áp dụng 2 lần. Chặn ở mức DB để không
        #     phụ thuộc vào thời điểm ở phía app (services.get_or_create_active_attempt
        #     bắt IntegrityError rồi dùng chung Attempt đã có).
        constraints = [
            models.UniqueConstraint(
                fields=["chat_session"],
                condition=models.Q(completed_at__isnull=True),
                name="unique_active_attempt_per_session",
            )
        ]

    def __str__(self) -> str:
        return f"Attempt(session={self.chat_session_id}) hints={self.hint_count}"


class ChatMessage(BaseModel):
    class Sender(models.TextChoices):
        USER = "USER", "User"
        AI = "AI", "AI"

    class NodeType(models.TextChoices):
        STEP = "STEP", "Step Node"
        ANSWER = "ANSWER", "Answer Node"
        CHANGE_METHOD = "CHANGE_METHOD", "Change Method Node"

    class ParentConfidence(models.TextChoices):
        HIGH = "high", "High"
        LOW = "low", "Low"

    class StepKind(models.TextChoices):
        """
        JA: 思考ツリー上でのそのメッセージの位置づけ。
            NONE   … ステップにしない(相槌・AIの返答など)。チャットには残るが木には出ない。
            TRUNK  … 幹。当初の目的に向かって前進する大きなステップ。1, 2, 3... と採番される。
            BRANCH … 枝。既出ステップを掘り下げる小さな質問。親の番号に連ねて 3-1, 3-2 と採番される。
        VI: Vai trò của tin nhắn trên cây tư duy.
            NONE   … không phải bước (câu đệm, câu trả lời của AI). Vẫn ở trong chat nhưng không lên cây.
            TRUNK  … thân. Bước lớn tiến tới mục tiêu ban đầu. Đánh số 1, 2, 3...
            BRANCH … nhánh. Câu hỏi nhỏ đào sâu một bước đã có. Đánh số nối theo cha: 3-1, 3-2.
        """

        NONE = "NONE", "ステップにしない / Không phải bước"
        TRUNK = "TRUNK", "幹(大きなステップ) / Thân (bước lớn)"
        BRANCH = "BRANCH", "枝(派生した質問) / Nhánh (câu hỏi phái sinh)"

    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name="messages")
    parent_message = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children",
    )

    suggested_parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        help_text="JA: AIが推定した親ノード / VI: Node cha do AI đề xuất",
    )
    parent_confidence = models.CharField(
        max_length=10,
        choices=ParentConfidence.choices,
        blank=True,
        help_text="JA: 親ノード推定の確信度 / VI: Độ tin cậy của việc đoán node cha",
    )
    parent_confirmed = models.BooleanField(
        default=True,
        help_text=(
            "JA: True=親ノードが確定済み(ユーザー明示指定 or 確認済み)。"
            "False=AI推定のみで未確認、フロントで確認UIを出す必要あり。"
            " VI: True=node cha đã chốt (user tự chọn hoặc đã confirm)."
            " False=mới chỉ là AI đoán, chưa confirm, frontend cần hiển thị UI xác nhận."
        ),
    )

    sender = models.CharField(max_length=10, choices=Sender.choices)
    message_text = models.TextField()
    is_hint = models.BooleanField(default=False)
    node_type = models.CharField(max_length=20, choices=NodeType.choices, default=NodeType.STEP)

    # JA: ★思考ツリー上の位置づけ。これが NONE のメッセージは木に現れない。
    #     以前は全てのユーザー発言が無条件にステップ化されていたため、「そうですね」
    #     のような相槌までノードになっていた。その判定をここで表現する。
    # VI: ★Vai trò trên cây tư duy. Tin nhắn có giá trị NONE sẽ không hiện trên cây.
    #     Trước đây mọi phát ngôn của user đều thành bước vô điều kiện, nên cả câu đệm
    #     như "そうですね" cũng thành node. Trường này biểu thị phán đoán đó.
    step_kind = models.CharField(
        max_length=10,
        choices=StepKind.choices,
        default=StepKind.NONE,
        help_text="JA: 幹/枝/ステップ外の区別 / VI: Phân biệt thân / nhánh / không phải bước",
    )
    # JA: ★ノードに表示する短いタイトル。ユーザーの発言そのままではなく要約。
    #     回答生成と同じ1回のAI呼び出しでまとめて受け取るため、追加のAPIコストは無い。
    # VI: ★Tiêu đề ngắn hiển thị trên node, là bản tóm tắt chứ không phải nguyên văn phát ngôn.
    #     Nhận chung trong cùng 1 lần gọi AI với việc sinh câu trả lời nên không tốn thêm chi phí API.
    step_title = models.CharField(
        max_length=120,
        blank=True,
        default="",
        help_text="JA: ノードに表示する要約タイトル / VI: Tiêu đề tóm tắt hiển thị trên node",
    )

    def __str__(self) -> str:
        return f"[{self.sender}] {self.message_text[:30]}"
