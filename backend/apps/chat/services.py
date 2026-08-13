# JA: チャット機能と知識ツリー連携の業務ロジック
# VI: Logic nghiệp vụ kết nối giữa tính năng Chat và Cây kiến thức

import logging
from django.utils import timezone
from apps.common.exceptions import ValidationError
from apps.reviews.models import KnowledgeNode, ReviewLog 
from .models import ChatSession, ChatMessage

logger = logging.getLogger(__name__)


def create_chat_session_for_node(*, user, node_id: int = None, title: str = "New Study Session") -> ChatSession:
    """
    JA: 知識ノードに基づいて新しいチャットセッション(ATTEMPT)を作成します。
    VI: Tạo phiên chat (ATTEMPT) mới gắn liền với 1 Node trên Cây kiến thức.
    """
    node = None
    if node_id:
        node = KnowledgeNode.objects.filter(id=node_id).first()
        if not node:
            logger.error("JA: 指定された KnowledgeNode が存在しません: %s / VI: KnowledgeNode được chỉ định không tồn tại: %s", node_id, node_id)
            raise ValidationError("Knowledge Node không tồn tại / 該当する知識ノードが存在しません。")
            
        if title == "New Study Session":
            title = f"Học: {node.title}"

    session = ChatSession.objects.create(
        user=user,
        knowledge_node=node,
        title=title,
        hint_count=0
    )
    logger.info("JA: 新しい ATTEMPT セッションを作成しました (ID: %s) / VI: Đã tạo phiên ATTEMPT mới (ID: %s)", session.id, session.id)
    return session


def record_hint_or_completion(*, session: ChatSession, action_type: str):
    """
    JA: ヒントカウントの更新および学習完了ログ (REVIEW_LOG) の記録を行う。
    VI: Cập nhật số lần xin gợi ý và ghi nhận nhật ký hoàn thành (REVIEW_LOG).
    """
    # JA: 1. ヒント要求時のカウント増加処理
    # VI: 1. Xử lý tăng số lần gợi ý khi người dùng yêu cầu HINT
    if action_type == "HINT":
        session.hint_count += 1
        session.save(update_fields=['hint_count'])
        logger.info("JA: セッション %s のヒント回数を更新: %s / VI: Cập nhật số hint cho session %s: %s", session.id, session.hint_count, session.id, session.hint_count)

    # JA: 2. 学習完了時の REVIEW_LOG 作成処理
    # VI: 2. Xử lý tạo REVIEW_LOG khi hoàn thành bài học
    if action_type == "COMPLETE":
        session.completed_at = timezone.now()
        session.save(update_fields=['completed_at'])

        # JA: ノードが存在する場合のみ復習ログを作成
        # VI: Chỉ tạo log ôn tập nếu phiên này gắn với 1 Node kiến thức
        if session.knowledge_node:
            # JA: ヒント使用回数に基づくパフォーマンス評価の算出 (1〜5段階)
            # VI: Tính điểm đánh giá hiệu suất dựa trên số lần dùng gợi ý (Thang 1-5)
            if session.hint_count == 0:
                rating = 5  # JA: 完璧 / VI: Hoàn hảo
            elif session.hint_count <= 2:
                rating = 3  # JA: 普通 / VI: Trung bình
            else:
                rating = 1  # JA: 要復習 / VI: Yếu (Cần ôn lại)

            # JA: ERD に基づいて REVIEW_LOG を作成
            # VI: Tạo REVIEW_LOG theo đúng sơ đồ ERD
            ReviewLog.objects.create(
                attempt=session,
                performance_rating=rating,
                response_time_seconds=60  # JA: 仮の応答時間 / VI: Thời gian phản hồi tạm tính
            )
            logger.info("JA: REVIEW_LOG を作成しました (Session ID: %s, Rating: %s) / VI: Đã tạo REVIEW_LOG (Session ID: %s, Rating: %s)", session.id, rating, session.id, rating)