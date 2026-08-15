"""
JA: 認可・入力検証・services呼び出し・シリアライズのみ。業務ロジックは書かない。
VI: Chỉ phân quyền, kiểm tra đầu vào, gọi services, tuần tự hóa. Không viết
    logic nghiệp vụ ở đây.
"""

from django.utils import timezone
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import ReviewSchedule
from .serializers import ReviewScheduleSerializer


class ReviewScheduleViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = ReviewScheduleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ReviewSchedule.objects.filter(node__topic__user=self.request.user).select_related(
            "node", "node__topic"
        )

    @action(detail=False, methods=["get"])
    def due(self, request):
        # JA: 予定日が古い(=放置が長い)ものから並べる。ユーザーが上から順に
        #     片付ければ、木の緑が戻るのが早い。
        # VI: Sắp xếp từ hạn cũ nhất (bỏ quên lâu nhất). User xử lý lần lượt từ trên
        #     xuống thì cây xanh lại nhanh hơn.
        queryset = (
            self.get_queryset()
            .filter(next_review_at__lte=timezone.now())
            .order_by("next_review_at")
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
