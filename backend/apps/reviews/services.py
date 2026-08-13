"""
JA: 間隔反復アルゴリズム(SM-2)の実装。問題文(KnowledgeNode)は復習のたびに
    AIが新しく生成するが、復習スケジュール(ReviewSchedule)は生成された
    使い捨てのノードではなく、その生成元となった「常設の概念ノード」
    (origin_node)に対して更新する。このAIは正誤判定(is_correct)を行わ
    ないため、performance_rating(0〜5)は Attempt.hint_count から算出する。
VI: Triển khai thuật toán lặp lại ngắt quãng (SM-2). Nội dung bài toán
    (KnowledgeNode) được AI tạo mới mỗi lần ôn tập, nhưng lịch ôn tập
    (ReviewSchedule) được cập nhật vào "node khái niệm cố định"
    (origin_node) sinh ra nó, chứ không phải node dùng một lần đó. Vì AI
    này không chấm đúng/sai (is_correct), performance_rating (0-5) được
    tính từ Attempt.hint_count.
"""

from datetime import timedelta

from django.utils import timezone

from apps.ai.base import ChatMessage
from apps.ai.client import get_llm
from apps.common.exceptions import ValidationError
from apps.topics import services as topics_services
from apps.topics.models import KnowledgeNode

from .models import ReviewSchedule

MIN_EASINESS_FACTOR = 1.3
PASSING_RATING = 3  # これ未満は「想起失敗」として扱う(SM-2の標準的な閾値)


def resolve_schedule_node(node: KnowledgeNode) -> KnowledgeNode:
    """
    ReviewSchedule を持つべき常設ノードを返す。

    node がAI生成の類題(origin_nodeを持つ)であれば、その元になった
    常設ノードを返す。node自身が常設ノード(origin_nodeがNone)であれば、
    そのまま自分自身を返す。
    """
    return node.origin_node or node


def get_or_create_schedule(node: KnowledgeNode) -> ReviewSchedule:
    """
    常設ノードの ReviewSchedule を取得する。まだ無ければ初期値で作成する
    (トピックに新しいノードを追加した直後などは、まだ一度も復習して
    いないので ReviewSchedule が存在しない)。
    """
    target_node = resolve_schedule_node(node)
    schedule, _created = ReviewSchedule.objects.get_or_create(node=target_node)
    return schedule


def rating_from_hint_count(hint_count: int) -> int:
    """
    ヒント使用数から performance_rating(0〜5)を算出する。

    このAIは正誤判定を行わないため、completed_at が記録された Attempt は
    「最終的には解決できた」ことを意味する。そのぶん、ヒントを何回
    使ったかを記憶定着の強さの代理指標として使う。5回目以降は易しい
    ヒントに切り替わる仕様(対話機能側)と閾値を揃えている。
    """
    if hint_count <= 0:
        return 5  # ヒントなしで完了 = 完全に定着
    elif hint_count == 1:
        return 4
    elif hint_count <= 3:
        return 3
    elif hint_count <= 5:
        return 2  # 易しいヒントへの切り替え境界
    return 1  # 易しいヒントに切り替わってもなお多くの手順が必要だった


def apply_sm2(node: KnowledgeNode, performance_rating: int) -> ReviewSchedule:
    """
    SM-2アルゴリズムに基づき、常設ノードの ReviewSchedule を更新する。

    Args:
        node: Attempt.node(AI生成の類題、または常設ノードそのもの)
        performance_rating: 0〜5の記憶定着度評価

    Returns:
        実際に更新された ReviewSchedule(origin_nodeがあればそちら側)
    """
    if not 0 <= performance_rating <= 5:
        raise ValidationError("performance_rating must be between 0 and 5")

    schedule = get_or_create_schedule(node)

    if performance_rating < PASSING_RATING:
        # 想起に失敗 -> 連続成功回数をリセットし、間隔も最初からやり直す
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


def record_review_result(attempt) -> ReviewSchedule:
    """
    Attempt完了時にチャット機能側から呼ばれるエントリーポイント。

    performance_rating は外から受け取らず、attempt.hint_count から
    このモジュール内で算出する(算出方法が変わっても呼び出し側の
    コードには影響しない)。

    - attempt.node.origin_node がある(=AI生成の類題を解いた)場合のみ
      ReviewLog を作成する。origin_node が無い(=常設ノードを直接解いた
      = 対話機能での初回学習)場合は ReviewLog は作らず、SM-2の更新だけ行う。
    - SM-2の更新自体は、初回学習・復習のどちらでも常に行う。
    """
    from .models import ReviewLog  # アプリ間の循環importを避けるため関数内import

    performance_rating = rating_from_hint_count(attempt.hint_count)

    if attempt.node.origin_node is not None:
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

    return apply_sm2(attempt.node, performance_rating)


def start_review(user, source_node: KnowledgeNode):
    """
    間隔復習機能から、対話機能(チャットセッション)へ処理を引き継ぐ入口。

    Attempt・ChatSession の作成はチャット機能側の責務なので、ここでは
    生成した類題ノードを作ったうえで、チャット機能の start_attempt() に
    「誰が(user)」「どのノードを解くか(node_id)」だけを渡す。

    渡さないもの(あえて渡さない):
    - 問題文・タイトルなどのノードの中身
        -> チャット機能が node_id から自分で KnowledgeNode を取得すればよく、
           二重に渡すと片方だけ更新されたときにズレる原因になる
    - このAttemptが復習由来かどうかを示すフラグ
        -> node.origin_node の有無で判定できるので不要
    - performance_rating の計算方法
        -> record_review_result() 側の責務であり、開始時点では関係ない
    """
    from apps.chat.services import start_attempt  # アプリ間の循環importを避けるため関数内import

    generated_node = generate_similar_problem(source_node)
    return start_attempt(user=user, node_id=generated_node.id)


def generate_similar_problem(source_node: KnowledgeNode) -> KnowledgeNode:
    """
    source_node を基に、AIで類題を1件生成してDBに保存する。
    生成したノードの origin_node は source_node を指す。

    apps.ai.client.get_llm() 経由で呼ぶため、fake / gemini のどちらが
    設定されていても呼び出し側(このコード)は変更不要。
    """
    llm = get_llm()
    messages = [
        ChatMessage(
            role="system",
            content=(
                "あなたは学習アプリの問題作成アシスタントです。"
                "与えられた元の課題と同じ概念・難易度を問う類題を1問作成してください。"
                "1行目にタイトル、2行目以降に問題本文だけを出力してください。"
                "前置きや解説は不要です。"
            ),
        ),
        ChatMessage(
            role="user",
            content=f"元の課題タイトル: {source_node.title}\n元の課題本文:\n{source_node.content}",
        ),
    ]
    result = llm.chat(messages)

    lines = result.text.strip().splitlines()
    title = lines[0].strip() if lines else f"{source_node.title}(類題)"
    content = "\n".join(lines[1:]).strip() or result.text.strip()

    # JA: KnowledgeNodeの構造への書き込みは topics アプリの責務なので、
    #     直接 create せず services 経由で依頼する。
    # VI: Ghi vào cấu trúc KnowledgeNode là trách nhiệm của app topics, nên
    #     không create trực tiếp mà nhờ qua services của app đó.
    return topics_services.create_derived_node(
        origin_node=source_node,
        title=title,
        content=content,
    )