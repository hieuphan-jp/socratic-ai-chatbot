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

    def __str__(self) -> str:
        return f"[{self.sender}] {self.message_text[:30]}"
