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

from django.db.models import Q

from apps.common.exceptions import NotFound, PermissionDenied, ValidationError

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


def get_owned_topic(*, user, topic_id) -> Topic:
    """
    JA: 他アプリ(例: apps/chat)がTopicを所有権チェック込みで取得するための窓口。
        Topicモデルへの直接クエリは他アプリにさせず、この関数経由に一本化する。
    VI: Cửa ngõ để app khác (vd: apps/chat) lấy Topic kèm kiểm tra chủ sở hữu.
        Không cho app khác query trực tiếp model Topic; phải qua hàm này.
    """
    topic = Topic.objects.filter(id=topic_id, user=user).first()
    if topic is None:
        raise NotFound("Topic が見つかりません / Không tìm thấy Topic")
    return topic


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
    VI: Gom cây phân cấp Topic của user + KnowledgeNode thuộc mỗi Topic,
        trả về theo định dạng TreeNode của frontend.
        【Thay đổi thiết kế】Vì origin_node đã bị xóa và mọi node đều là
        node cố định, việc lọc theo origin_node__isnull=True trước đây
        không còn cần nữa.
    """
    topics = list(Topic.objects.filter(user=user).order_by("position", "created_at"))
    nodes = list(KnowledgeNode.objects.filter(topic__user=user).order_by("created_at"))

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


def get_topic_children(*, topic: Topic) -> tuple[list[Topic], list[KnowledgeNode]]:
    """
    JA: 検索セッションのドリルダウンUI用。指定Topic直下の子Topicと、直属の
        KnowledgeNodeを返す。
        【設計変更】origin_node__isnull=Trueの絞り込みは不要になった。
    VI: Dùng cho UI duyệt sâu dần của phiên tìm kiếm. Trả về Topic con trực
        tiếp và KnowledgeNode trực thuộc topic.
        【Thay đổi thiết kế】Không còn cần lọc origin_node__isnull=True.
    """
    child_topics = list(Topic.objects.filter(parent=topic).order_by("position", "created_at"))
    nodes = list(KnowledgeNode.objects.filter(topic=topic).order_by("created_at"))
    return child_topics, nodes


def _descendant_topic_ids(topic: Topic) -> list:
    """
    JA: topic自身を含む、配下すべてのTopic idを再帰的に集める(検索範囲の特定用)。
        同一userのTopicをまとめて1回で取得し、Python側で親子関係を辿ることで
        深さ分だけクエリを発行するのを避ける。
    VI: Thu thập id của chính topic và toàn bộ Topic con cháu (đệ quy), dùng để
        xác định phạm vi tìm kiếm. Lấy一次 toàn bộ Topic của cùng user rồi duyệt
        quan hệ cha/con ở phía Python để tránh tốn 1 query cho mỗi tầng sâu.
    """
    all_topics = Topic.objects.filter(user_id=topic.user_id).only("id", "parent_id")
    children_by_parent: dict = {}
    for t in all_topics:
        children_by_parent.setdefault(t.parent_id, []).append(t.id)

    ids = [topic.id]
    stack = [topic.id]
    while stack:
        current = stack.pop()
        for child_id in children_by_parent.get(current, []):
            ids.append(child_id)
            stack.append(child_id)
    return ids


def search_knowledge_nodes(*, topic: Topic, query: str) -> list[KnowledgeNode]:
    """
    JA: topic配下(自身を含む)を再帰的に検索し、title/contentにqueryを含む
        KnowledgeNodeを返す。
        【設計変更】origin_node__isnull=Trueの絞り込みは不要になった
        (AI生成の使い捨て類題自体が存在しなくなったため)。
    VI: Tìm đệ quy trong phạm vi topic (bao gồm chính nó), trả về
        KnowledgeNode có title/content chứa query.
        【Thay đổi thiết kế】Không còn cần lọc origin_node__isnull=True
        (vì node類題 dùng một lần do AI sinh không còn tồn tại nữa).
    """
    query = (query or "").strip()
    if not query:
        raise ValidationError("q is required")

    topic_ids = _descendant_topic_ids(topic)
    return list(
        KnowledgeNode.objects.filter(topic_id__in=topic_ids)
        .filter(Q(title__icontains=query) | Q(content__icontains=query))
        .order_by("created_at")
    )
