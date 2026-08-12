"""
apps/topics/models.py

JA: 学習木構造のテーブル定義のみ（テーブル構造。業務ロジックは services.py）。
    Topic はカテゴリ（棚）で自己参照の親子関係を持ち、KnowledgeNode は実際に
    学んだ内容（本）で Topic に属する。KnowledgeNode の SM-2 用フィールドは
    apps/reviews の ReviewSchedule に分離し、ここには構造のみを持たせる。
VI: Chỉ định nghĩa cấu trúc bảng của cây học tập (logic nghiệp vụ ở services.py).
    Topic là danh mục (kệ sách), có quan hệ cha/con tự tham chiếu. KnowledgeNode
    là nội dung đã học thực tế (cuốn sách), thuộc về một Topic. Các trường cho
    SM-2 tách sang ReviewSchedule của apps/reviews; ở đây chỉ giữ cấu trúc.
"""

from django.conf import settings
from django.db import models

from apps.common.models import BaseModel


class Topic(BaseModel):
    # JA: 所有者。get_queryset で必ず絞る / VI: Chủ sở hữu; luôn lọc trong get_queryset
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="topics"
    )
    # JA: 親トピック。NULLならルート / VI: Topic cha. NULL nghĩa là gốc
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="children"
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    # JA: 兄弟内の表示順序。作成時に services.py が末尾番号を採番する
    # VI: Thứ tự hiển thị giữa các anh em. services.py cấp số ở cuối khi tạo
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["position", "created_at"]

    def __str__(self) -> str:
        return self.name


class KnowledgeNode(BaseModel):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="nodes")
    # JA: AI生成の類題の場合、生成元の常設ノードを指す / VI: Nếu là bài AI sinh, trỏ tới node cố định gốc
    origin_node = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="derived_nodes"
    )
    title = models.CharField(max_length=255)
    content = models.TextField()

    class Meta:
        ordering = ["created_at"]

    def __str__(self) -> str:
        return self.title
