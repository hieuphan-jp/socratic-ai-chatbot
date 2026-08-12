"""
JA: 認可・入力検証・services呼び出し・シリアライズのみ。業務ロジックは書かない。
VI: Chỉ phân quyền, kiểm tra đầu vào, gọi services, tuần tự hóa. Không viết
    logic nghiệp vụ ở đây.
"""

from django.utils import timezone
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.common.exceptions import NotFound
from apps.topics.models import KnowledgeNode

from . import services
from .models import ReviewSchedule
from .serializers import ReviewScheduleSerializer, StartReviewSerializer


class ReviewScheduleViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = ReviewScheduleSerializer
    permission_classes = [IsAuthenticated]
    # JA: IsOwner(apps.common.permissions)は今回追加しない。retrieve/update/
    #     destroyが無くget_object()を呼ばないため、object単位の権限チェックが
    #     そもそも発火しない。所有者絞り込みはget_querysetとstart()内の明示
    #     チェックで担保している。
    # VI: Không thêm IsOwner ở đây. Vì không có retrieve/update/destroy nên
    #     get_object() không được gọi, permission theo object sẽ không kích
    #     hoạt. Việc lọc theo chủ sở hữu đã được đảm bảo qua get_queryset và
    #     kiểm tra tường minh trong start().

    def get_queryset(self):
        # JA: ★所有者絞り込み(必須)。ノードの所属Topic経由でuserを辿る
        # VI: ★Lọc theo chủ sở hữu (bắt buộc). Đi qua Topic của node để lấy user
        return ReviewSchedule.objects.filter(
            node__topic__user=self.request.user
        ).select_related("node", "node__topic")

    @action(detail=False, methods=["get"])
    def due(self, request):
        """
        JA: 復習タイミングを判定し、期限が来ているものだけ返す。
        VI: Xác định thời điểm ôn tập, chỉ trả về những cái đã đến hạn.
        """
        queryset = self.get_queryset().filter(next_review_at__lte=timezone.now())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def start(self, request):
        """
        JA: 復習を開始する。類題を生成し、対話機能(チャットセッション)に
            引き継ぐ。渡すのは user と node_id だけ。
        VI: Bắt đầu ôn tập. Tạo bài tương tự rồi bàn giao cho tính năng đối
            thoại (chat session). Chỉ truyền user và node_id.
        """
        serializer = StartReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # JA: 所有者チェック。他人のノードは復習開始できない
        # VI: Kiểm tra chủ sở hữu. Không được bắt đầu ôn tập node của người khác
        source_node = KnowledgeNode.objects.filter(
            id=serializer.validated_data["node_id"],
            topic__user=request.user,
        ).first()
        if source_node is None:
            raise NotFound("KnowledgeNode not found")

        attempt = services.start_review(user=request.user, source_node=source_node)
        return Response(
            {
                "attempt_id": attempt.id,
                "chat_session_id": attempt.chat_session.id,
            },
            status=status.HTTP_201_CREATED,
        )