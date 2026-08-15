"""
JA: 間隔反復アルゴリズム(SM-2)の実装。
VI: Triển khai thuật toán lặp lại ngắt quãng (SM-2).
"""

from datetime import timedelta

from django.utils import timezone

from apps.common.exceptions import ValidationError
from apps.topics.models import KnowledgeNode

from .models import ReviewSchedule

MIN_EASINESS_FACTOR = 1.3
PASSING_RATING = 3

# JA: 【設計変更 2026-08-15】理解度の自己申告(understood)は廃止した。
#     AIは理解の確認をしない方針であり、復習の成否は「予定日に自分でノードを
#     見に行って完了ボタンを押したかどうか」だけで判断する。よって完了は常に
#     この固定評価で記録する(将来もっと柔軟な評価に戻せるよう、ReviewLogの
#     performance_rating フィールド自体は残してある)。
# VI: 【Thay đổi thiết kế 2026-08-15】Đã bỏ việc user tự khai mức hiểu
#     (understood). AI không hỏi kiểm tra mức hiểu; việc ôn tập thành công hay
#     không chỉ căn cứ vào "user có tự mở lại node đúng hạn và bấm nút hoàn
#     thành hay không". Vì vậy mọi lần hoàn thành đều ghi bằng điểm cố định này
#     (vẫn giữ field performance_rating của ReviewLog để sau này quay lại cách
#     đánh giá linh hoạt hơn).
COMPLETION_RATING = 5


def get_or_create_schedule(node: KnowledgeNode) -> ReviewSchedule:
    schedule, _created = ReviewSchedule.objects.get_or_create(node=node)
    return schedule


def apply_sm2(node: KnowledgeNode, performance_rating: int) -> ReviewSchedule:
    if not 0 <= performance_rating <= 5:
        raise ValidationError("performance_rating must be between 0 and 5")

    schedule = get_or_create_schedule(node)

    if performance_rating < PASSING_RATING:
        schedule.repetitions = 0
        schedule.interval_days = 1
    else:
        schedule.repetitions += 1
        if schedule.repetitions == 1:
            schedule.interval_days = 1
        elif schedule.repetitions == 2:
            schedule.interval_days = 6
        else:
            schedule.interval_days = round(schedule.interval_days * schedule.easiness_factor)

    ef = schedule.easiness_factor + (
        0.1 - (5 - performance_rating) * (0.08 + (5 - performance_rating) * 0.02)
    )
    schedule.easiness_factor = max(MIN_EASINESS_FACTOR, ef)

    now = timezone.now()
    schedule.next_review_at = now + timedelta(days=schedule.interval_days)
    schedule.last_learned_at = now
    schedule.learned_count += 1

    schedule.save(
        update_fields=[
            "repetitions",
            "interval_days",
            "easiness_factor",
            "next_review_at",
            "last_learned_at",
            "learned_count",
            "updated_at",
        ]
    )
    return schedule


def record_review_result(attempt, understood: bool | None = None) -> ReviewSchedule:
    """
    JA: 1回分の学習/復習(Attempt)が完了したことを記録し、次回の復習日を更新する。
        引数 understood は廃止済み(COMPLETION_RATING 参照)。呼び出し側(apps/chat)
        がまだ渡してくるため受け取るだけ受け取り、無視する。チャット機能側の
        改修が入ったら引数ごと削除してよい。
    VI: Ghi nhận một lượt học/ôn tập (Attempt) đã hoàn thành và cập nhật ngày ôn
        kế tiếp. Tham số understood đã bỏ (xem COMPLETION_RATING). Vì bên gọi
        (apps/chat) vẫn còn truyền vào nên chỉ nhận rồi bỏ qua. Khi phía tính năng
        Chat được sửa thì có thể xóa hẳn tham số này.
    """
    from .models import ReviewLog

    node = attempt.chat_session.knowledge_node
    if node is None:
        raise ValidationError(
            "このセッションにはKnowledgeNodeが紐づいていません / "
            "Session này chưa gắn với KnowledgeNode nào"
        )

    performance_rating = COMPLETION_RATING

    response_time_seconds = None
    if attempt.completed_at and attempt.created_at:
        response_time_seconds = int((attempt.completed_at - attempt.created_at).total_seconds())

    ReviewLog.objects.create(
        attempt=attempt,
        performance_rating=performance_rating,
        response_time_seconds=response_time_seconds,
    )

    return apply_sm2(node, performance_rating)
