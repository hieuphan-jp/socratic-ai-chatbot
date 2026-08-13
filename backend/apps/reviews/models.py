"""
JA: 間隔反復のスケジュール(ReviewSchedule)と、復習した際の記録(ReviewLog)。
    ReviewScheduleはKnowledgeNodeへの1:1で、「常設ノード」(origin_nodeを
    持たないノード)にのみ意味を持つ。AI生成の使い捨て類題ノードは
    ReviewScheduleを持たない(常に生成元のスケジュールを参照・更新する)。
VI: Lịch ôn tập ngắt quãng (ReviewSchedule) và bản ghi mỗi lần ôn tập
    (ReviewLog). ReviewSchedule có quan hệ 1:1 với KnowledgeNode, chỉ có ý
    nghĩa với "node cố định" (node không có origin_node). Node類題 do AI
    sinh ra dùng một lần thì không có ReviewSchedule riêng (luôn tham
    chiếu/cập nhật lịch của node gốc).
"""

from django.db import models
from django.utils import timezone

from apps.common.models import BaseModel
from apps.chat.models import Attempt
from apps.topics.models import KnowledgeNode


class ReviewSchedule(BaseModel):
    node = models.OneToOneField(
        KnowledgeNode,
        on_delete=models.CASCADE,
        related_name="review_schedule",
        help_text="常設ノード(origin_nodeを持たないノード)であること",
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
    attempt = models.ForeignKey(
        Attempt,
        on_delete=models.CASCADE,
        related_name="review_logs",
    )
    performance_rating = models.IntegerField(
        choices=[(i, str(i)) for i in range(6)],
        help_text="hint_countから算出した0〜5の記憶定着度評価",
    )
    response_time_seconds = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"ReviewLog(attempt={self.attempt_id}, rating={self.performance_rating})"