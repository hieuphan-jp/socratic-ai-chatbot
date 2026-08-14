"""
JA: ReviewSchedule のJSON表現。保存処理や業務判断はここに書かない
    (services.py の責務)。
VI: Biểu diễn JSON của ReviewSchedule. Không viết xử lý lưu hay phán đoán
    nghiệp vụ ở đây (đó là trách nhiệm của services.py).
"""

from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from .models import ReviewSchedule


class ReviewScheduleSerializer(serializers.ModelSerializer):
    node_id = serializers.UUIDField(source="node.id", read_only=True)
    node_title = serializers.CharField(source="node.title", read_only=True)
    topic_id = serializers.UUIDField(source="node.topic_id", read_only=True)
    retention_level = serializers.CharField(read_only=True)
    retention_color = serializers.CharField(read_only=True)
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
        try:
            return obj.node.chat_session.id
        except ObjectDoesNotExist:
            return None
