"""
JA: 間隔反復のスケジュール(ReviewSchedule)と、復習した際の記録(ReviewLog)。
    【設計変更 2026-08-13 その1】復習はAIが新しい類題を生成する形ではなく、
    知識ノードが生まれた元のChatSession(1ノードにつき1セッション)に入り
    直して続きを対話する形に変わった。そのため「常設ノード/AI生成の
    使い捨てノード」という区別(origin_node)はreviews側では使わなくなった。
    ReviewScheduleはKnowledgeNode 1件につき1件、単純な1:1で持つ。
    【設計変更 2026-08-13 その2】1つのChatSessionを何度も復習に使い回す
    ため、「何回目の復習か」を区別する apps.chat.models.Attempt が新設
    された。ReviewLogはChatSessionではなくこのAttemptを参照する。
VI: Lịch ôn tập ngắt quãng (ReviewSchedule) và bản ghi mỗi lần ôn tập
    (ReviewLog). 【Thay đổi thiết kế 2026-08-13, phần 1】Ôn tập không còn
    là AI sinh bài tương tự mới, mà là mở lại ChatSession gốc (1 node ứng
    với 1 session) và tiếp tục hội thoại ở đó. Vì vậy sự phân biệt "node
    cố định / node dùng một lần do AI sinh" (origin_node) không còn được
    dùng ở phía reviews nữa. ReviewSchedule có quan hệ 1:1 đơn giản với
    từng KnowledgeNode.
    【Thay đổi thiết kế 2026-08-13, phần 2】Vì dùng lại 1 ChatSession
    nhiều lần để ôn tập, nên đã thêm mới apps.chat.models.Attempt để phân
    biệt "lần ôn tập thứ mấy". ReviewLog tham chiếu Attempt này thay vì
    ChatSession.
"""

from django.db import models
from django.utils import timezone

from apps.chat.models import Attempt
from apps.common.models import BaseModel
from apps.topics.models import KnowledgeNode


class ReviewSchedule(BaseModel):
    node = models.OneToOneField(
        KnowledgeNode,
        on_delete=models.CASCADE,
        related_name="review_schedule",
    )

    # --- 間隔反復アルゴリズム(SM-2)用フィールド ---
    easiness_factor = models.FloatField(
        default=2.5, help_text="難易度係数(最小値1.3を目安にアプリ側でバリデーション)"
    )
    interval_days = models.IntegerField(default=0, help_text="次回復習までの日数間隔")
    repetitions = models.IntegerField(default=0, help_text="連続で完了できた回数")
    next_review_at = models.DateTimeField(
        default=timezone.now, help_text="復習問題を出題する予定日時"
    )

    # --- 記憶定着の可視化用フィールド ---
    last_learned_at = models.DateTimeField(
        null=True, blank=True, help_text="最後に学習(挑戦・復習)した日時"
    )
    learned_count = models.PositiveIntegerField(
        default=0,
        help_text=(
            "学習した回数の累計。SM-2の repetitions と違い、"
            "失敗しても0にリセットしない"
        ),
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"ReviewSchedule(node={self.node_id})"

    # --- 記憶定着の濃さ(色)は保存せず、都度この2フィールドから計算する ---
    RETENTION_COLORS = {
        "unlearned": "#9E9E9E",
        "fresh": "#2E7D46",
        "fading": "#7FB894",
        "overdue": "#C9622A",
    }

    @property
    def retention_level(self) -> str:
        """経過日数と interval_days の比率から定着度合いを4段階で返す。"""
        if self.last_learned_at is None:
            return "unlearned"

        elapsed_days = (timezone.now() - self.last_learned_at).days
        decay_ratio = elapsed_days / max(self.interval_days, 1)

        if decay_ratio <= 0.5:
            return "fresh"
        elif decay_ratio <= 1.0:
            return "fading"
        return "overdue"

    @property
    def retention_color(self) -> str:
        return self.RETENTION_COLORS[self.retention_level]


class ReviewLog(BaseModel):
    # JA: apps.chat.models.Attempt(1回分の学習・復習の記録)を参照する。
    #     1つのChatSessionを何度も復習に使い回すため、ChatSessionを直接
    #     指すと「何回目の復習か」を区別できなくなる(2回目の記録が1回目を
    #     上書きしてしまう)。Attemptがその区別を担う。
    # VI: Tham chiếu apps.chat.models.Attempt (bản ghi cho 1 lần học/ôn
    #     tập). Vì dùng lại 1 ChatSession nhiều lần để ôn tập, nếu trỏ
    #     thẳng vào ChatSession sẽ không phân biệt được "lần ôn tập thứ
    #     mấy" (lần 2 sẽ ghi đè lần 1). Attempt đảm nhiệm việc phân biệt đó.
    attempt = models.ForeignKey(
        Attempt,
        on_delete=models.CASCADE,
        related_name="review_logs",
    )
    performance_rating = models.IntegerField(
        choices=[(i, str(i)) for i in range(6)],
        help_text="ユーザーの自己申告(理解できたか)から算出した0〜5の記憶定着度評価",
    )
    response_time_seconds = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"ReviewLog(attempt={self.attempt_id}, rating={self.performance_rating})"