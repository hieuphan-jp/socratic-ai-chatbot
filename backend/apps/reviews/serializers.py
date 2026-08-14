"""
JA: ReviewSchedule のJSON表現。保存処理や業務判断はここに書かない
    (services.py の責務)。
    【設計変更 2026-08-13】復習開始(AI類題生成→新規セッション作成)は
    廃止したため、StartReviewSerializerは削除した。代わりに、復習は
    「元のChatSessionに戻る」形になったので、そのセッションIDを返す。
VI: Biểu diễn JSON của ReviewSchedule. Không viết xử lý lưu hay phán đoán
    nghiệp vụ ở đây (đó là trách nhiệm của services.py).
    【Thay đổi thiết kế 2026-08-13】Đã bỏ việc bắt đầu ôn tập (AI sinh bài
    tương tự → tạo session mới) nên xóa StartReviewSerializer. Thay vào
    đó, ôn tập là "quay lại ChatSession gốc" nên trả về id của session đó.
"""

from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from .models import ReviewSchedule


class ReviewScheduleSerializer(serializers.ModelSerializer):
    # JA: フロントが木構造の色分け・復習画面で必要な、ノード側の情報も併せて返す
    # VI: Trả kèm thông tin phía node, cần cho việc tô màu cây và màn hình ôn tập
    node_id = serializers.UUIDField(source="node.id", read_only=True)
    node_title = serializers.CharField(source="node.title", read_only=True)
    topic_id = serializers.UUIDField(source="node.topic_id", read_only=True)
    retention_level = serializers.CharField(read_only=True)
    retention_color = serializers.CharField(read_only=True)
    # JA: ⑥「過去のチャットセッションに入る」ためのID。knowledge_nodeが
    #     OneToOneFieldになったため、1ノードにつき必ず1セッション
    #     (無ければnull)。
    # VI: id để "quay lại ChatSession trước đó" (⑥). Vì knowledge_node là
    #     OneToOneField nên 1 node chắc chắn ứng với 1 session (null nếu
    #     chưa có).
    chat_session_id = serializers.SerializerMethodField()

    class Meta:
        model = ReviewSchedule
        fields = [
            "id",
            "node_id",
            "node_title",
            "topic_id",
            "interval_days",
            "next_review_at",
            "learned_count",
            "retention_level",
            "retention_color",
            "chat_session_id",
        ]
        read_only_fields = fields

    def get_chat_session_id(self, obj):
        # JA: ChatSession.knowledge_node が OneToOneField なので、逆参照は
        #     単数(obj.node.chat_session)。まだ一度もセッションが作られて
        #     いない場合は RelatedObjectDoesNotExist になるため try/except。
        # VI: ChatSession.knowledge_node là OneToOneField nên truy cập
        #     ngược là số ít (obj.node.chat_session). Nếu chưa từng tạo
        #     session sẽ ném RelatedObjectDoesNotExist nên cần try/except.
        try:
            return obj.node.chat_session.id
        except ObjectDoesNotExist:
            return None