"""
JA: 間隔反復アルゴリズム(SM-2)の実装。
    【設計変更 2026-08-13 その1】復習はAIによる類題生成をやめ、知識ノードが
    生まれた元のChatSession(1ノードにつき1セッション、OneToOne)に入り
    直して続きを対話する形になった。generate_similar_problem・
    resolve_schedule_nodeは廃止した。
    【設計変更 2026-08-13 その2】1つのChatSessionを何度も復習に使い回す
    ため、「何回目の復習か」を区別する apps.chat.models.Attempt
    (ChatSessionへのFK、hint_count・completed_atを持つ)が新設された。
    ReviewLogはこのAttemptを参照する。
    【設計変更 2026-08-13 その3】performance_ratingはヒント使用数からで
    はなく、ユーザー自身が「分かった/分からなかった」と自己申告する
    understood(真偽値)から決める。連続で「分かった」と確認できた回数は
    SM-2のrepetitionsがそのまま数えるので、別途カウンタは持たない。
VI: Triển khai thuật toán lặp lại ngắt quãng (SM-2).
    【Thay đổi thiết kế 2026-08-13, phần 1】Ôn tập không còn là AI sinh bài
    tương tự mới, mà là mở lại ChatSession gốc (1 node ứng với 1 session,
    OneToOne) và tiếp tục hội thoại ở đó. Đã bỏ generate_similar_problem/
    resolve_schedule_node.
    【Thay đổi thiết kế 2026-08-13, phần 2】Vì dùng lại 1 ChatSession nhiều
    lần để ôn tập, nên đã thêm mới apps.chat.models.Attempt (FK tới
    ChatSession, có hint_count/completed_at) để phân biệt "lần ôn tập thứ
    mấy". ReviewLog tham chiếu Attempt này.
    【Thay đổi thiết kế 2026-08-13, phần 3】performance_rating không tính
    từ số lần dùng gợi ý, mà từ việc người dùng tự báo "đã hiểu/chưa hiểu"
    (understood, boolean). Số lần liên tiếp xác nhận "đã hiểu" đã được
    repetitions của SM-2 tự đếm, nên không cần thêm bộ đếm riêng.
"""

from datetime import timedelta

from django.utils import timezone

from apps.common.exceptions import ValidationError
from apps.topics.models import KnowledgeNode

from .models import ReviewSchedule

MIN_EASINESS_FACTOR = 1.3
PASSING_RATING = 3  # これ未満は「想起失敗」として扱う(SM-2の標準的な閾値)

# JA: understood(真偽値)をSM-2のperformance_rating(0〜5)へ単純変換する。
#     0〜5の細かい粒度はもう使わないが、ReviewLog.performance_ratingの
#     フィールド定義(0〜5のIntegerField)は変えずに済ませるため、この
#     2値だけを割り当てている。
# VI: Quy đổi đơn giản understood (boolean) sang performance_rating (0-5)
#     của SM-2. Không còn dùng độ chi tiết 0-5 nữa, nhưng để không phải
#     đổi định nghĩa field ReviewLog.performance_rating (IntegerField
#     0-5), chỉ gán 2 giá trị này.
RATING_UNDERSTOOD = 5
RATING_NOT_UNDERSTOOD = 1


def get_or_create_schedule(node: KnowledgeNode) -> ReviewSchedule:
    """
    node の ReviewSchedule を取得する。まだ無ければ初期値で作成する
    (ノード作成直後などは、まだ一度も学習していないので存在しない)。
    """
    schedule, _created = ReviewSchedule.objects.get_or_create(node=node)
    return schedule


def rating_from_understood(understood: bool) -> int:
    """
    ユーザーの自己申告(理解できたか)から performance_rating を決める。
    """
    return RATING_UNDERSTOOD if understood else RATING_NOT_UNDERSTOOD


def apply_sm2(node: KnowledgeNode, performance_rating: int) -> ReviewSchedule:
    """
    SM-2アルゴリズムに基づき、node の ReviewSchedule を更新する。

    Args:
        node: 学習・復習の対象になったKnowledgeNode
        performance_rating: 0〜5の記憶定着度評価
            (rating_from_understood()の出力を渡す想定)

    Returns:
        更新された ReviewSchedule
    """
    if not 0 <= performance_rating <= 5:
        raise ValidationError("performance_rating must be between 0 and 5")

    schedule = get_or_create_schedule(node)

    if performance_rating < PASSING_RATING:
        # 想起に失敗 -> 連続成功回数をリセットし、間隔も最初からやり直す
        schedule.repetitions = 0
        schedule.interval_days = 1
    else:
        # JA: ここでのrepetitions+1が、「連続で分かったと確認できた回数」の
        #     カウントに相当する。
        # VI: repetitions+1 ở đây chính là bộ đếm "số lần liên tiếp xác
        #     nhận đã hiểu".
        schedule.repetitions += 1
        if schedule.repetitions == 1:
            schedule.interval_days = 1
        elif schedule.repetitions == 2:
            schedule.interval_days = 6
        else:
            schedule.interval_days = round(
                schedule.interval_days * schedule.easiness_factor
            )

    # easiness_factor の更新(SM-2の標準式)
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
    """
    Attempt完了時にチャット機能側(record_hint_or_completion)から
    呼ばれるエントリーポイント。

    Args:
        attempt: 完了した apps.chat.models.Attempt(1回分の学習・復習の記録)
        understood: ユーザーが「理解できた」と自己申告したかどうか

    初回学習・復習(同じセッションへの再入場)のどちらでも、区別せず常に
    ReviewLog を作成し SM-2 を更新する。
    """
    from .models import ReviewLog  # アプリ間の循環importを避けるため関数内import

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