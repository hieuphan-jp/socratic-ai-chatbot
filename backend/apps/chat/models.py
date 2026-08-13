# JA: Chat機能のモデル定義。KNOWLEDGE_NODE / ReviewLog 連携 + 分岐推定用フィールド
# VI: Định nghĩa model Chat. Tích hợp KNOWLEDGE_NODE / ReviewLog + các trường phục vụ đoán nhánh

from django.conf import settings
from django.db import models
from apps.common.models import BaseModel
from apps.topics.models import KnowledgeNode  # JA: 知識ツリーノード / VI: Node cây kiến thức


class ChatSession(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chat_sessions",
    )
    title = models.CharField(max_length=255, default="New Chat Session")

    # JA: KNOWLEDGE_NODE への外部キー（どのノードの学習か）
    # VI: Khoá ngoại tới KNOWLEDGE_NODE (Xác định phiên chat thuộc Node kiến thức nào)
    knowledge_node = models.ForeignKey(
        KnowledgeNode,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="attempts",
    )

    # JA: 間隔復習 (SM-2) 計算用の学習データ
    # VI: Dữ liệu học tập phục vụ tính toán lặp lại ngắt quãng (SM-2)
    hint_count = models.IntegerField(default=0, help_text="Số lần xin gợi ý")
    completed_at = models.DateTimeField(null=True, blank=True, help_text="Thời gian hoàn thành")

    def __str__(self) -> str:
        return f"{self.user.username} - {self.title}"


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

    session = models.ForeignKey(
        ChatSession, on_delete=models.CASCADE, related_name="messages"
    )
    parent_message = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children",
    )

    # JA: ★分岐推定用フィールド（復元）。AI が推定した親ノードを parent_message とは
    #     別に保持する。ユーザーが確認/変更するまで parent_message はこの推定値を
    #     「仮」の値として採用した状態になる。
    # VI: ★Các field phục vụ đoán nhánh (khôi phục lại). Node cha do AI đề xuất,
    #     lưu tách riêng khỏi parent_message chính thức. Cho tới khi user xác nhận/
    #     đổi lại, parent_message sẽ tạm dùng đúng giá trị AI đề xuất này.
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
            "JA: True=親ノードが確定済み（ユーザー明示指定 or 確認済み）。"
            "False=AI推定のみで未確認、フロントで確認UIを出す必要あり。"
            " VI: True=node cha đã chốt (user tự chọn hoặc đã confirm)."
            " False=mới chỉ là AI đoán, chưa confirm, frontend cần hiện UI xác nhận."
        ),
    )

    sender = models.CharField(max_length=10, choices=Sender.choices)
    message_text = models.TextField()
    is_hint = models.BooleanField(default=False)
    node_type = models.CharField(
        max_length=20, choices=NodeType.choices, default=NodeType.STEP
    )

    def __str__(self) -> str:
        return f"[{self.sender}] {self.message_text[:30]}"


# JA: reviews アプリからの参照用に Attempt として ChatSession を定義
# VI: Định nghĩa Attempt trỏ tới ChatSession để khớp với app reviews
Attempt = ChatSession