# JA: Chat機能のモデル定義。テーブル構造のみ管理
# VI: Định nghĩa model tính năng Chat. Chỉ quản lý cấu trúc bảng
from django.conf import settings
from django.db import models

from apps.common.models import BaseModel  # UUID PK + timestamps
from apps.topics.models import KnowledgeNode


class Attempt(BaseModel):
    # JA: KnowledgeNode 1件に対する1回の挑戦。hint_count・completed_at を
    #     どのタイミングで更新するか(ヒント送信のたびに+1する、ユーザーが
    #     「理解できた」と申告したときにcompleted_atをセットする、等)は
    #     チャット機能側の実装に委ねる。ここではテーブル構造のみ定義する。
    # VI: Một lần thử cho 1 KnowledgeNode. Việc cập nhật hint_count/
    #     completed_at vào lúc nào (mỗi lần gửi gợi ý thì +1, khi người dùng
    #     báo "đã hiểu" thì set completed_at, v.v.) do phía tính năng chat tự
    #     triển khai. Ở đây chỉ định nghĩa cấu trúc bảng.
    node = models.ForeignKey(
        KnowledgeNode, on_delete=models.CASCADE, related_name="attempts"
    )
    hint_count = models.PositiveIntegerField(default=0)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return f"Attempt({self.node_id}) hints={self.hint_count}"


class ChatSession(BaseModel):
    # JA: 所有者。get_queryset で必ず絞る / VI: Chủ sở hữu; luôn lọc trong get_queryset
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="chat_sessions"
    )
    title = models.CharField(max_length=255, default="New Chat Session")

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

    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name="messages")
    parent_message = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, related_name="children"
    )
    sender = models.CharField(max_length=10, choices=Sender.choices)
    message_text = models.TextField()
    is_hint = models.BooleanField(default=False)
    node_type = models.CharField(max_length=20, choices=NodeType.choices, default=NodeType.STEP)

    def __str__(self) -> str:
        return f"[{self.sender}] {self.message_text[:30]}"