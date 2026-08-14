"""
apps/topics/serializers.py

JA: JSONの形の定義と入力検証のみ。保存処理・業務判断は services.py の責務。
VI: Chỉ định nghĩa hình dạng JSON và kiểm tra đầu vào. Lưu/phán đoán nghiệp vụ
    thuộc trách nhiệm của services.py.
"""

from rest_framework import serializers

from .models import KnowledgeNode, Topic


class TopicSerializer(serializers.ModelSerializer):
    # JA: 子Topic・直属の常設KnowledgeNodeのどちらかがあればTrue。検索セッションの
    #     ドリルダウンUIが「これ以上開けるか」を判定するために使う。
    #     TopicViewSet.get_queryset() の annotate(has_child_topics/has_nodes) が無い
    #     インスタンス(例: 作成直後のレスポンス)ではFalse扱いになる(=作成直後は子が無いので正しい)。
    # VI: True nếu có Topic con hoặc KnowledgeNode cố định trực thuộc. Dùng để UI
    #     duyệt sâu dần biết "còn mở được nữa không". Với instance chưa được
    #     annotate(has_child_topics/has_nodes) từ TopicViewSet.get_queryset() (vd:
    #     response ngay sau khi tạo) sẽ coi là False (đúng vì vừa tạo thì chưa có con).
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
        # JA: user/position はサーバが決める → read_only / VI: user/position do server quyết → read_only
        read_only_fields = ["id", "user", "position", "created_at", "has_children"]

    def get_has_children(self, obj) -> bool:
        return bool(getattr(obj, "has_child_topics", False) or getattr(obj, "has_nodes", False))


class KnowledgeNodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = KnowledgeNode
        fields = ["id", "topic", "origin_node", "title", "content", "created_at"]
        # JA: origin_node は AI生成専用(create_derived_node)が設定 → read_only
        # VI: origin_node chỉ do create_derived_node (AI sinh) thiết lập → read_only
        read_only_fields = ["id", "origin_node", "created_at"]


class KnowledgeNodeSummarySerializer(serializers.ModelSerializer):
    """
    JA: 検索セッションの一覧・検索結果用の軽量表現(本文を含まない)。
    VI: Biểu diễn gọn cho danh sách/kết quả tìm kiếm của phiên tìm kiếm (không có nội dung).
    """

    class Meta:
        model = KnowledgeNode
        fields = ["id", "title", "topic"]
        read_only_fields = fields


class KnowledgeNodeDetailSerializer(serializers.ModelSerializer):
    """JA: 課題詳細画面用。topic_name を併せて返す。VI: Dùng cho màn hình chi tiết bài toán, trả kèm topic_name."""

    topic_name = serializers.CharField(source="topic.name", read_only=True)

    class Meta:
        model = KnowledgeNode
        fields = ["id", "title", "content", "topic", "topic_name"]
        read_only_fields = fields
