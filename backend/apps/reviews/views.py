"""
JA: 認可・入力検証・services呼び出し・シリアライズのみ。業務ロジックは書かない。
    【設計変更 2026-08-13】復習開始(AI類題生成→新規セッション作成)は
    廃止したため、startアクションは削除した。reviewsは「一覧を返す」
    「色を計算する」だけの受け身のアプリになった。実際の完了処理の
    トリガーはapps.chat側(record_hint_or_completion)から来る。
VI: Chỉ phân quyền, kiểm tra đầu vào, gọi services, tuần tự hóa. Không viết
    logic nghiệp vụ ở đây.
    【Thay đổi thiết kế 2026-08-13】Đã bỏ việc bắt đầu ôn tập (AI sinh bài
    tương tự → tạo session mới) nên xóa action start. reviews giờ chỉ là
    app bị động: trả về danh sách, tính màu sắc. Trigger hoàn thành thực
    tế đến từ phía apps.chat (record_hint_or_completion).
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
    # JA: IsOwner(apps.common.permissions)は追加しない。IsOwnerはobj.user_id
    #     を直接見るが、ReviewScheduleはuserを直接持たない
    #     (node.topic.user経由)ため、付けると常に拒否される。retrieve等が
    #     無くget_object()を呼ばないため、そもそもobject単位の権限チェックが
    #     発火しない。所有者絞り込みはget_querysetで担保している。
    # VI: Không thêm IsOwner (apps.common.permissions). IsOwner đọc trực
    #     tiếp obj.user_id, nhưng ReviewSchedule không có user trực tiếp
    #     (phải qua node.topic.user) nên nếu thêm sẽ luôn bị từ chối. Không
    #     có retrieve nên get_object() không được gọi, permission theo
    #     object vốn không kích hoạt. Việc lọc theo chủ sở hữu đã được đảm
    #     bảo qua get_queryset.

    def get_queryset(self):
        # JA: ★所有者絞り込み(必須)。ノードの所属Topic経由でuserを辿る
        #     絞り込みなしの一覧(list)が④(木全体の色分け)に使われる想定。
        # VI: ★Lọc theo chủ sở hữu (bắt buộc). Đi qua Topic của node để lấy
        #     user. Danh sách không lọc gì (list) dự kiến dùng cho ④ (tô màu
        #     toàn bộ cây).
        return ReviewSchedule.objects.filter(node__topic__user=self.request.user).select_related(
            "node", "node__topic"
        )

    @action(detail=False, methods=["get"])
    def due(self, request):
        """
        JA: 復習タイミングを判定し、期限が来ているものだけ返す
            (⑤で優先的に見せたいノードの絞り込み用)。
        VI: Xác định thời điểm ôn tập, chỉ trả về những cái đã đến hạn
            (dùng để lọc các node nên ưu tiên hiển thị ở ⑤).
        """
        queryset = self.get_queryset().filter(next_review_at__lte=timezone.now())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
