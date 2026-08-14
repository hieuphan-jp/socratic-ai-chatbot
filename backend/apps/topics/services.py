"""
apps/topics/services.py

JA: 学習木構造の業務ロジック(HTTP非依存)。KnowledgeNodeの構造
    (topic/title/content)への書き込みは、このモジュール経由に一本化する。
    【設計変更 2026-08-13】復習機能がAIによる類似問題生成をやめたため、
    create_derived_node は廃止した。全てのKnowledgeNodeが常設ノードに
    なったため、build_learning_tree の origin_node による絞り込みも
    不要になった。
VI: Logic nghiệp vụ của cây học tập (không phụ thuộc HTTP). Việc ghi vào
    cấu trúc KnowledgeNode (topic/title/content) gom về một mối qua
    module này.
    【Thay đổi thiết kế 2026-08-13】Vì tính năng ôn tập không còn AI sinh
    bài tương tự nữa, đã bỏ create_derived_node. Vì mọi KnowledgeNode giờ
    đều là node cố định, việc lọc theo origin_node trong
    build_learning_tree cũng không cần nữa.
"""

from apps.common.exceptions import PermissionDenied, ValidationError

from .models import KnowledgeNode, Topic


def _next_position(*, user, parent: Topic | None) -> int:
    last = Topic.objects.filter(user=user, parent=parent).order_by("-position").first()
    return (last.position + 1) if last else 0


def create_topic(*, user, name: str, description: str = "", parent: Topic | None = None) -> Topic:
    name = (name or "").strip()
    if not name:
        raise ValidationError("名前は必須です / Tên là bắt buộc")
    if parent is not None and parent.user_id != user.id:
        raise PermissionDenied(
            "他人のTopic配下には作成できません / Không thể tạo dưới Topic của người khác"
        )
    return Topic.objects.create(
        user=user,
        parent=parent,
        name=name,
        description=(description or "").strip(),
        position=_next_position(user=user, parent=parent),
    )


def create_knowledge_node(*, user, topic: Topic, title: str, content: str) -> KnowledgeNode:
    if topic.user_id != user.id:
        raise PermissionDenied(
            "他人のTopicには追加できません / Không thể thêm vào Topic của người khác"
        )
    title = (title or "").strip()
    if not title:
        raise ValidationError("タイトルは必須です / Tiêu đề là bắt buộc")
    return KnowledgeNode.objects.create(topic=topic, title=title, content=content or "")


def build_learning_tree(*, user) -> list[dict]:
    """
    JA: user配下の Topic階層 + 各Topicに属する KnowledgeNode を、フロントの
        TreeNode形式にまとめて返す。
        【設計変更】origin_nodeが廃止され全ノードが常設ノードになったため、
        以前あった origin_node__isnull=True による絞り込みは不要になった。
    VI: Gom cây phân cấp Topic của user + KnowledgeNode thuộc từng Topic,
        trả về theo định dạng TreeNode của frontend.
        【Thay đổi thiết kế】Vì origin_node đã bị xóa và mọi node đều là
        node cố định, việc lọc theo origin_node__isnull=True trước đây
        không còn cần nữa.
    """
    topics = list(Topic.objects.filter(user=user).order_by("position", "created_at"))
    nodes = list(
        KnowledgeNode.objects.filter(topic__user=user).order_by("created_at")
    )

    nodes_by_topic: dict[str, list[KnowledgeNode]] = {}
    for node in nodes:
        nodes_by_topic.setdefault(str(node.topic_id), []).append(node)

    children_by_parent: dict[str | None, list[Topic]] = {}
    for topic in topics:
        key = str(topic.parent_id) if topic.parent_id else None
        children_by_parent.setdefault(key, []).append(topic)

    def build(topic: Topic) -> dict:
        child_topics = [build(t) for t in children_by_parent.get(str(topic.id), [])]
        leaf_nodes = [
            {"id": str(n.id), "label": n.title, "type": "knowledge_node"}
            for n in nodes_by_topic.get(str(topic.id), [])
        ]
        children = child_topics + leaf_nodes
        result: dict = {"id": str(topic.id), "label": topic.name, "type": "topic"}
        if children:
            result["children"] = children
        return result

    return [build(t) for t in children_by_parent.get(None, [])]