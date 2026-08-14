"""
apps/topics/views.py

JA: 認可・入力検証・services呼び出し・シリアライズのみ。業務ロジックは書かない。
VI: Chỉ phân quyền, kiểm tra đầu vào, gọi services, tuần tự hóa. Không viết
    logic nghiệp vụ ở đây.
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
        # JA: ★所有者絞り込み（必須）。has_children算出用にannotateしておく。
        # VI: ★Lọc theo chủ sở hữu (bắt buộc). Annotate sẵn để tính has_children.
        has_child_topics = Topic.objects.filter(parent=OuterRef("pk"))
        has_nodes = KnowledgeNode.objects.filter(topic=OuterRef("pk"), origin_node__isnull=True)
        queryset = Topic.objects.filter(user=self.request.user).annotate(
            has_child_topics=Exists(has_child_topics),
            has_nodes=Exists(has_nodes),
        )
        # JA: 検索セッションの起点(ルートTopicのみ)を取得するためのオプション絞り込み。
        #     list アクション限定。children/search/retrieveはself.get_object()経由で
        #     このget_queryset()を共有するため、ここで絞ると「クエリに?parent=nullが
        #     付いていた」だけで本来アクセスできる自分のTopicが404になってしまう。
        # VI: Lọc tùy chọn để lấy điểm bắt đầu phiên tìm kiếm (chỉ Topic gốc). Chỉ áp
        #     dụng cho action list. children/search/retrieve dùng chung get_queryset()
        #     này qua self.get_object(), nếu lọc ở đây thì chỉ vì query có ?parent=null
        #     mà Topic của chính mình (đáng lẽ truy cập được) sẽ bị trả về 404.
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
        """
        JA: 指定Topic直下の子Topicと常設KnowledgeNodeを返す(ドリルダウンUI用)。
        VI: Trả về Topic con và KnowledgeNode cố định trực thuộc (dùng cho UI duyệt sâu dần).
        """
        topic = self.get_object()
        child_topics, nodes = services.get_topic_children(topic=topic)
        # JA: has_children を反映するため、annotate済みのget_queryset()経由で取り直す。
        # VI: Lấy lại qua get_queryset() đã annotate để có has_children.
        annotated_children = self.get_queryset().filter(id__in=[t.id for t in child_topics])
        return Response(
            {
                "topics": TopicSerializer(annotated_children, many=True).data,
                "nodes": KnowledgeNodeSummarySerializer(nodes, many=True).data,
            }
        )

    @action(detail=True, methods=["get"])
    def search(self, request, pk=None):
        """
        JA: 指定Topic配下(自身を含む)を再帰的に検索し、常設KnowledgeNodeを返す。
        VI: Tìm đệ quy trong phạm vi Topic (bao gồm chính nó), trả về KnowledgeNode cố định.
        """
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
    viewsets.GenericViewSet,
):
    serializer_class = KnowledgeNodeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # JA: ★所有者絞り込み（必須）。KnowledgeNodeにuser列はないためtopic経由で辿る
        # VI: ★Lọc theo chủ sở hữu (bắt buộc). KnowledgeNode không có cột user nên đi qua topic
        return KnowledgeNode.objects.filter(topic__user=self.request.user)

    def get_serializer_class(self):
        # JA: 詳細取得のみtopic_name付きの表現に切り替える(検索結果から選んだ後の画面用)。
        # VI: Chỉ đổi sang biểu diễn có topic_name khi lấy chi tiết (dùng cho màn hình sau khi chọn từ kết quả tìm kiếm).
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
