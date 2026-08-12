"""
JA: ReviewSchedule のJSON表現と、復習開始リクエストの入力検証。
    保存処理や業務判断はここに書かない(services.py の責務)。
VI: Biểu diễn JSON của ReviewSchedule và kiểm tra đầu vào cho yêu cầu bắt
    đầu ôn tập. Không viết xử lý lưu hay phán đoán nghiệp vụ ở đây (đó là
    trách nhiệm của services.py).
"""

from rest_framework import serializers

from apps.topics.models import KnowledgeNode

from .models import ReviewSchedule


class ReviewScheduleSerializer(serializers.ModelSerializer):
    # JA: フロントが復習範囲を選ぶ画面で必要な、ノード側の情報も併せて返す
    # VI: Trả kèm thông tin phía node, cần cho màn hình chọn phạm vi ôn tập
    node_id = serializers.UUIDField(source="node.id", read_only=True)
    node_title = serializers.CharField(source="node.title", read_only=True)
    topic_id = serializers.UUIDField(source="node.topic_id", read_only=True)
    retention_level = serializers.CharField(read_only=True)
    retention_color = serializers.CharField(read_only=True)

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
        ]
        read_only_fields = fields


class StartReviewSerializer(serializers.Serializer):
    # JA: 復習対象として選んだ常設ノードのID(検索セッション/分類ツリーで選択済み)
    # VI: id của node cố định được chọn để ôn tập (đã chọn ở phiên tìm kiếm/cây phân loại)
    node_id = serializers.UUIDField()

    def validate_node_id(self, value):
        if not KnowledgeNode.objects.filter(id=value).exists():
            raise serializers.ValidationError("KnowledgeNode not found")
        return value