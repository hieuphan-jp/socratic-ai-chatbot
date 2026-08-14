"""
apps/topics/serializers.py

JA: JSONの形の定義と入力検証のみ。保存処理・業務判断は services.py の責務。
    【設計変更 2026-08-13】origin_nodeフィールドが削除されたため、
    KnowledgeNodeSerializer から origin_node への参照を削除した。
VI: Chỉ định nghĩa hình dạng JSON và kiểm tra đầu vào. Lưu/phán đoán nghiệp vụ
    thuộc trách nhiệm của services.py.
    【Thay đổi thiết kế 2026-08-13】Vì field origin_node đã bị xóa, đã xóa
    tham chiếu origin_node khỏi KnowledgeNodeSerializer.
"""

from rest_framework import serializers

from .models import KnowledgeNode, SearchHistory, Topic


class TopicSerializer(serializers.ModelSerializer):
    has_children = serializers.SerializerMethodField()

    class Meta:
        model = Topic
        fields = [
            "id",
            "user",
            "parent",
            "name",
            "description",
            "position",
            "created_at",
            "has_children",
        ]
        read_only_fields = ["id", "user", "position", "created_at", "has_children"]

    def get_has_children(self, obj) -> bool:
        return bool(getattr(obj, "has_child_topics", False) or getattr(obj, "has_nodes", False))


class KnowledgeNodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = KnowledgeNode
        fields = ["id", "topic", "title", "content", "created_at"]
        read_only_fields = ["id", "created_at"]


class KnowledgeNodeSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = KnowledgeNode
        fields = ["id", "title", "topic"]
        read_only_fields = fields


class KnowledgeNodeDetailSerializer(serializers.ModelSerializer):
    topic_name = serializers.CharField(source="topic.name", read_only=True)

    class Meta:
        model = KnowledgeNode
        fields = ["id", "title", "content", "topic", "topic_name"]
        read_only_fields = fields


class SearchHistorySerializer(serializers.ModelSerializer):
    """JA: 検索履歴の表示用。VI: Dùng để hiển thị lịch sử tìm kiếm."""

    topic_name = serializers.CharField(source="topic.name", read_only=True)

    class Meta:
        model = SearchHistory
        fields = ["id", "query", "topic", "topic_name", "created_at"]
        read_only_fields = fields


class AISearchInputSerializer(serializers.Serializer):
    """JA: AI検索の入力検証のみ。VI: Chỉ kiểm tra đầu vào của AI search."""

    description = serializers.CharField()
