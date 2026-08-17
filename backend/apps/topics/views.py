"""
apps/topics/views.py

JA: 認可・入力検証・services呼び出し・シリアライズのみ。業務ロジックは書かない。
    【設計変更 2026-08-13】origin_nodeフィールドが削除されたため、
    has_nodes の annotate から origin_node__isnull=True の絞り込みを外した。
VI: Chỉ phân quyền, kiểm tra đầu vào, gọi services, tuần tự hóa. Không viết
    logic nghiệp vụ ở đây.
    【Thay đổi thiết kế 2026-08-13】Vì field origin_node đã bị xóa, đã bỏ
    điều kiện lọc origin_node__isnull=True khỏi annotate của has_nodes.
"""

from django.db.models import Exists, OuterRef
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.permissions import IsOwner

from . import services
from .models import KnowledgeNode, SearchHistory, Topic
from .serializers import (
    AISearchInputSerializer,
    KnowledgeNodeDetailSerializer,
    KnowledgeNodeSerializer,
    KnowledgeNodeSummarySerializer,
    SearchHistorySerializer,
    TopicSerializer,
)


class TopicViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = TopicSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        has_child_topics = Topic.objects.filter(parent=OuterRef("pk"))
        has_nodes = KnowledgeNode.objects.filter(topic=OuterRef("pk"))
        queryset = Topic.objects.filter(user=self.request.user).annotate(
            has_child_topics=Exists(has_child_topics),
            has_nodes=Exists(has_nodes),
        )
        if self.action == "list" and self.request.query_params.get("parent") == "null":
            queryset = queryset.filter(parent__isnull=True)
        return queryset

    def perform_create(self, serializer):
        serializer.instance = services.create_topic(
            user=self.request.user,
            name=serializer.validated_data["name"],
            description=serializer.validated_data.get("description", ""),
            parent=serializer.validated_data.get("parent"),
        )

    @action(detail=True, methods=["get"])
    def children(self, request, pk=None):
        topic = self.get_object()
        child_topics, nodes = services.get_topic_children(topic=topic)
        annotated_children = self.get_queryset().filter(id__in=[t.id for t in child_topics])
        return Response(
            {
                "topics": TopicSerializer(annotated_children, many=True).data,
                "nodes": KnowledgeNodeSummarySerializer(nodes, many=True).data,
            }
        )

    @action(detail=True, methods=["get"])
    def search(self, request, pk=None):
        topic = self.get_object()
        results = services.search_knowledge_nodes(
            topic=topic, query=request.query_params.get("q", "")
        )
        return Response(KnowledgeNodeSummarySerializer(results, many=True).data)

    @action(detail=False, methods=["post"], url_path="ai-search")
    def ai_search(self, request):
        """
        JA: 単語がわからないユーザー向け。曖昧な説明文をAIに渡し、学習カテゴリ名の
            候補を提案するだけ(実際の検索は行わない)。
        VI: Dành cho user không nhớ từ chính xác. Đưa mô tả mơ hồ cho AI để gợi ý tên
            danh mục học tập (không tự thực hiện tìm kiếm).
        """
        serializer = AISearchInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        suggestions = services.suggest_topic_keyword(
            description=serializer.validated_data["description"]
        )
        return Response({"suggestions": suggestions})


class SearchHistoryViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """JA: 検索履歴の一覧のみ(新しい順)。VI: Chỉ liệt kê lịch sử tìm kiếm (mới nhất trước)."""

    serializer_class = SearchHistorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # JA: ★所有者絞り込み（必須）/ VI: ★Lọc theo chủ sở hữu (bắt buộc)
        return SearchHistory.objects.filter(user=self.request.user).select_related("topic")[
            : services.SEARCH_HISTORY_LIMIT
        ]


class KnowledgeNodeViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = KnowledgeNodeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # JA: ★所有権の絞り込み(必須、CONVENTIONS.md §1)。DestroyModelMixinの
        #     destroy()もget_object()経由でこのqueryset越しにしかノードを
        #     取得できないため、他人のノードを消せない安全性はここ1箇所で担保される。
        #     削除時の関連レコードの扱いはモデル側のon_deleteで決まる:
        #       ReviewSchedule(node)   … CASCADE  (葉が消えれば復習記録も消える)
        #       ChatSession(knowledge_node) … SET_NULL (会話自体は残り、フリーチャット扱いに戻る)
        # VI: ★Lọc theo chủ sở hữu (bắt buộc, CONVENTIONS.md §1). destroy() của
        #     DestroyModelMixin cũng chỉ lấy node qua get_object() dựa trên queryset
        #     này, nên chỉ cần lọc ở đây là đủ để không xóa được node của người khác.
        #     Cách xử lý bản ghi liên quan khi xóa do on_delete ở model quyết định:
        #       ReviewSchedule(node)   … CASCADE  (lá mất thì bản ghi ôn tập cũng mất)
        #       ChatSession(knowledge_node) … SET_NULL (hội thoại vẫn còn, quay về dạng chat tự do)
        return KnowledgeNode.objects.filter(topic__user=self.request.user)

    def get_serializer_class(self):
        if self.action == "retrieve":
            return KnowledgeNodeDetailSerializer
        return super().get_serializer_class()

    def perform_create(self, serializer):
        serializer.instance = services.create_knowledge_node(
            user=self.request.user,
            topic=serializer.validated_data["topic"],
            title=serializer.validated_data["title"],
            content=serializer.validated_data.get("content", ""),
        )


class LearningTreeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tree = services.build_learning_tree(user=request.user)
        return Response(tree)
