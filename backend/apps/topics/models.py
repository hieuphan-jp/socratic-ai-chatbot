"""
apps/topics/models.py

JA: 学習木構造のテーブル定義のみ(業務ロジックは services.py)。
    Topic はカテゴリ(棚)で自己参照の親子関係を持つ。KnowledgeNode は実際に
    学んだ内容(本)で Topic に属する。
    【設計変更 2026-08-13】復習機能がAIによる類似問題生成をやめたため、
    origin_node(類題ノードの出自を示すためだけのフィールド)は削除した。
    全てのKnowledgeNodeが常設ノードになる。
VI: Chỉ định nghĩa cấu trúc bảng của cây học tập (logic nghiệp vụ ở
    services.py). Topic là danh mục (kệ sách), có quan hệ cha/con tự
    tham chiếu. KnowledgeNode là nội dung đã học thực tế (cuốn sách),
    thuộc về một Topic.
    【Thay đổi thiết kế 2026-08-13】Vì tính năng ôn tập không còn AI sinh
    bài tương tự nữa, đã xóa origin_node (field chỉ dùng để đánh dấu
    nguồn gốc của node được sinh). Mọi KnowledgeNode giờ đều là node cố
    định.
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
    # JA: 兄弟間の表示順序。作成時に services.py が末尾番号を採番する
    # VI: Thứ tự hiển thị giữa các anh em. services.py cấp số ở cuối khi tạo
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["position", "created_at"]

    def __str__(self) -> str:
        return self.name


class KnowledgeNode(BaseModel):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="nodes")
    title = models.CharField(max_length=255)
    content = models.TextField()

    class Meta:
        ordering = ["created_at"]

    def __str__(self) -> str:
        return self.title
