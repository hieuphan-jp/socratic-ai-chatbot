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
from .models import KnowledgeNode, Topic
from .serializers import (
    KnowledgeNodeDetailSerializer,
    KnowledgeNodeSerializer,
    KnowledgeNodeSummarySerializer,
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


class KnowledgeNodeViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = KnowledgeNodeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
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
