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

RATING_UNDERSTOOD = 5
RATING_NOT_UNDERSTOOD = 1


def get_or_create_schedule(node: KnowledgeNode) -> ReviewSchedule:
    schedule, _created = ReviewSchedule.objects.get_or_create(node=node)
    return schedule


def rating_from_understood(understood: bool) -> int:
    return RATING_UNDERSTOOD if understood else RATING_NOT_UNDERSTOOD


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
            schedule.interval_days = round(
                schedule.interval_days * schedule.easiness_factor
            )

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


def record_review_result(attempt, understood: bool) -> ReviewSchedule:
    from .models import ReviewLog

    node = attempt.chat_session.knowledge_node
    if node is None:
        raise ValidationError(
            "このセッションにはKnowledgeNodeが紐づいていません / "
            "Session này chưa gắn với KnowledgeNode nào"
        )

    performance_rating = rating_from_understood(understood)

    response_time_seconds = None
    if attempt.completed_at and attempt.created_at:
        response_time_seconds = int(
            (attempt.completed_at - attempt.created_at).total_seconds()
        )

    ReviewLog.objects.create(
        attempt=attempt,
        performance_rating=performance_rating,
        response_time_seconds=response_time_seconds,
    )

    return apply_sm2(node, performance_rating)