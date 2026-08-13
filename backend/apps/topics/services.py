"""
apps/topics/services.py

JA: 学習木構造の業務ロジック（HTTP非依存）。KnowledgeNode の構造(topic/origin_node/
    title/content)への書き込みは、このモジュール経由に一本化する。他アプリ
    (例: apps/reviews)がAI生成の類題ノードを作りたい場合も create_derived_node
    を呼ぶこと。KnowledgeNode.objects.create を他アプリから直接呼ばない
    （所有権はこのアプリにあるため）。
VI: Logic nghiệp vụ của cây học tập (không phụ thuộc HTTP). Việc ghi vào cấu trúc
    KnowledgeNode (topic/origin_node/title/content) gom về một mối qua module này.
    App khác (vd: apps/reviews) muốn tạo node類題 do AI sinh cũng phải gọi
    create_derived_node. Không gọi thẳng KnowledgeNode.objects.create từ app khác
    (vì quyền sở hữu thuộc app này).
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


def create_derived_node(*, origin_node: KnowledgeNode, title: str, content: str) -> KnowledgeNode:
    """
    JA: AI生成の類題ノードを作成する。origin_node が常設ノードであることは
        呼び出し側(reviews)が保証する。
    VI: Tạo node類題 do AI sinh. Việc origin_node là node cố định do phía gọi
        (reviews) đảm bảo.
    """
    return KnowledgeNode.objects.create(
        topic=origin_node.topic,
        origin_node=origin_node,
        title=(title or "").strip() or f"{origin_node.title}(類題)",
        content=content or "",
    )


def build_learning_tree(*, user) -> list[dict]:
    """
    JA: user配下の Topic階層 + 各Topicに属する KnowledgeNode(常設ノードのみ、
        origin_node が NULL のもの)を、フロントの TreeNode 形式にまとめて返す。
        AI生成の使い捨て類題ノード(origin_node が非NULL)は木に含めない。
    VI: Gom cây phân cấp Topic của user + KnowledgeNode (chỉ node cố định,
        origin_node là NULL) thuộc mỗi Topic, trả về theo định dạng TreeNode
        của frontend. Không đưa node類題 dùng một lần do AI sinh (origin_node
        khác NULL) vào cây.
    """
    topics = list(Topic.objects.filter(user=user).order_by("position", "created_at"))
    nodes = list(
        KnowledgeNode.objects.filter(topic__user=user, origin_node__isnull=True).order_by(
            "created_at"
        )
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
