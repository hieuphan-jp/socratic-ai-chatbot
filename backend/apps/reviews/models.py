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
        help_text=("学習した回数の累計。SM-2の repetitions と違い、失敗しても0にリセットしない"),
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"ReviewSchedule(node={self.node_id})"

    # --- 定着度(緑の濃さ)と復習タイミング(別UI)は、別々の軸として返す ---
    # JA: 【設計変更 2026-08-15】以前は「経過日数 / interval_days」の比率ひとつで
    #     4段階の色(retention_level/retention_color)を決めていたが、それだと
    #     「復習を重ねて定着した」ことと「そろそろ復習の番が来た」ことが同じ色に
    #     混ざってしまい、ユーザーが木を見て何をすべきか分からなかった。そこで
    #     2軸に分ける:
    #       ・mastery_level … 復習を完了した累計回数。葉の緑の濃さに使う(増える一方)
    #       ・is_due        … 復習予定日を過ぎたか。緑とは別のUI(バッジ等)に使う
    #     色そのもの(16進コード)は表示の関心事なのでフロントで決める。ここでは
    #     段階の数(MASTERY_MAX_LEVEL)という業務上の閾値だけを持つ。
    # VI: 【Thay đổi thiết kế 2026-08-15】Trước đây chỉ dùng một tỉ lệ "số ngày đã
    #     trôi qua / interval_days" để quyết định 4 mức màu (retention_level/
    #     retention_color). Cách đó trộn lẫn "đã ôn nhiều lần nên nhớ chắc" với
    #     "sắp tới lượt ôn", khiến user nhìn cây không biết phải làm gì. Nay tách
    #     thành 2 trục:
    #       ・mastery_level … tổng số lần đã ôn xong; dùng cho độ đậm của màu xanh
    #       ・is_due        … đã quá hạn ôn chưa; dùng cho UI khác (badge...)
    #     Mã màu là việc của phía hiển thị nên frontend tự quyết. Ở đây chỉ giữ
    #     ngưỡng nghiệp vụ là số bậc (MASTERY_MAX_LEVEL).

    # JA: 何回復習したら「最も濃い緑(定着済み)」とみなすか。VI: Ôn bao nhiêu lần thì coi là "xanh đậm nhất".
    MASTERY_MAX_LEVEL = 5

    @property
    def mastery_level(self) -> int:
        """
        JA: 葉の緑の濃さ。0(未学習)〜MASTERY_MAX_LEVEL。学習/復習を完了するたびに
            1段階濃くなり、下がることはない。
        VI: Độ đậm màu xanh của lá. 0 (chưa học) đến MASTERY_MAX_LEVEL. Mỗi lần
            học/ôn xong đậm thêm 1 bậc và không bao giờ giảm.
        """
        return min(self.learned_count, self.MASTERY_MAX_LEVEL)

    @property
    def is_due(self) -> bool:
        """JA: 復習予定日を過ぎたか / VI: Đã tới (quá) hạn ôn tập chưa"""
        return self.next_review_at <= timezone.now()

    @property
    def days_overdue(self) -> int:
        """
        JA: 予定日から何日過ぎたか(まだ来ていなければ0)。「そろそろ」と「かなり
            放置している」をUIで出し分けたい場合に使う。
        VI: Đã quá hạn bao nhiêu ngày (chưa tới hạn thì 0). Dùng khi muốn phân biệt
            "sắp tới hạn" và "bỏ quên đã lâu" trên UI.
        """
        delta = timezone.now() - self.next_review_at
        return max(delta.days, 0)


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
