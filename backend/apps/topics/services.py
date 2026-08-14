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

import re

from django.db.models import Q

from apps.ai.base import ChatMessage
from apps.ai.client import get_llm
from apps.common.exceptions import PermissionDenied, ValidationError

from .models import KnowledgeNode, SearchHistory, Topic

# JA: AIに候補単語を出させるためのプロンプト。前置き無しでカンマ区切り1行だけを
#     出力させることで、パース処理を単純に保つ。
# VI: Prompt để AI đưa ra từ ứng viên. Yêu cầu chỉ xuất 1 dòng phân tách bằng dấu phẩy,
#     không lời dẫn, để việc parse ở phía sau đơn giản.
_AI_SEARCH_SYSTEM_PROMPT = (
    "あなたは学習用語の名付けアシスタントです。ユーザーは調べたい分野や概念の"
    "名前を思い出せず、曖昧な説明しかできません。説明から、学習カテゴリ名として"
    "使われそうな短い単語(名詞)の候補を1〜5個、カンマ区切りで1行だけ出力してください。"
    "説明や前置きは一切不要です。"
)


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


def get_topic_children(*, topic: Topic) -> tuple[list[Topic], list[KnowledgeNode]]:
    """
    JA: 検索セッションのドリルダウンUI用。指定Topic直下の子Topicと、直属の
        常設KnowledgeNode(origin_nodeがNULLのもの)を返す。
    VI: Dùng cho UI duyệt sâu dần của phiên tìm kiếm. Trả về Topic con trực tiếp
        và KnowledgeNode cố định (origin_node là NULL) trực thuộc topic.
    """
    child_topics = list(Topic.objects.filter(parent=topic).order_by("position", "created_at"))
    nodes = list(
        KnowledgeNode.objects.filter(topic=topic, origin_node__isnull=True).order_by("created_at")
    )
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
        常設KnowledgeNode(origin_nodeがNULLのもの)を返す。AI生成の使い捨て
        類題は検索セッションには出さない。
    VI: Tìm đệ quy trong phạm vi topic (bao gồm chính nó), trả về KnowledgeNode
        cố định (origin_node là NULL) có title/content chứa query. Không đưa
        node類題 dùng một lần do AI sinh vào phiên tìm kiếm.
    """
    query = (query or "").strip()
    if not query:
        raise ValidationError("q is required")

    # JA: 履歴記録は検索そのものの成否に影響させない副作用として最後に行う。
    # VI: Việc ghi lịch sử là tác dụng phụ, đặt sau cùng, không ảnh hưởng kết quả tìm kiếm.
    SearchHistory.objects.create(user_id=topic.user_id, topic=topic, query=query)

    topic_ids = _descendant_topic_ids(topic)
    return list(
        KnowledgeNode.objects.filter(topic_id__in=topic_ids, origin_node__isnull=True)
        .filter(Q(title__icontains=query) | Q(content__icontains=query))
        .order_by("created_at")
    )


# JA: 検索履歴として保持する最大件数(時系列スタック表示用)。SearchHistoryViewSet側で使う。
# VI: Số lượng tối đa giữ lại trong lịch sử tìm kiếm (dùng cho hiển thị kiểu ngăn xếp
#     theo thời gian). Dùng ở phía SearchHistoryViewSet.
SEARCH_HISTORY_LIMIT = 50


def suggest_topic_keyword(*, description: str) -> list[str]:
    """
    JA: 単語がわからないユーザーが曖昧な言葉で説明した内容から、AIに学習カテゴリ名の
        候補を1〜5個提案させる。実際の検索は行わず、候補単語のリストだけを返す
        (呼び出し側が別途 /api/topics/{id}/search/ を叩く想定)。
    VI: Từ mô tả mơ hồ của user không nhớ tên chính xác, nhờ AI gợi ý 1-5 từ ứng viên
        cho tên danh mục học tập. Không tự tìm kiếm, chỉ trả về danh sách từ ứng viên
        (bên gọi tự dùng để gọi riêng /api/topics/{id}/search/).
    """
    description = (description or "").strip()
    if not description:
        raise ValidationError("description is required")

    llm = get_llm()
    messages = [
        ChatMessage(role="system", content=_AI_SEARCH_SYSTEM_PROMPT),
        ChatMessage(role="user", content=description),
    ]
    result = llm.chat(messages)

    # JA: カンマ・読点・改行のいずれで区切られても対応し、重複を除きつつ順序維持、
    #     最大5件に絞る。
    # VI: Chấp nhận phân tách bằng dấu phẩy, dấu phẩy tiếng Nhật hoặc xuống dòng;
    #     loại trùng nhưng giữ thứ tự, giới hạn tối đa 5 mục.
    candidates = [c.strip() for c in re.split(r"[,、\n]", result.text) if c.strip()]
    seen: set[str] = set()
    unique: list[str] = []
    for candidate in candidates:
        if candidate not in seen:
            seen.add(candidate)
            unique.append(candidate)
    return unique[:5]
