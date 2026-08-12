"""
apps/topics/views.py

JA: 認可・入力検証・services呼び出し・シリアライズのみ。業務ロジックは書かない。
VI: Chỉ phân quyền, kiểm tra đầu vào, gọi services, tuần tự hóa. Không viết
    logic nghiệp vụ ở đây.
"""

from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.permissions import IsOwner

from . import services
from .models import KnowledgeNode, Topic
from .serializers import KnowledgeNodeSerializer, TopicSerializer


class TopicViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = TopicSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        # JA: ★所有者絞り込み（必須）/ VI: ★Lọc theo chủ sở hữu (bắt buộc)
        return Topic.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.instance = services.create_topic(
            user=self.request.user,
            name=serializer.validated_data["name"],
            description=serializer.validated_data.get("description", ""),
            parent=serializer.validated_data.get("parent"),
        )


class KnowledgeNodeViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = KnowledgeNodeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # JA: ★所有者絞り込み（必須）。KnowledgeNodeにuser列はないためtopic経由で辿る
        # VI: ★Lọc theo chủ sở hữu (bắt buộc). KnowledgeNode không có cột user nên đi qua topic
        return KnowledgeNode.objects.filter(topic__user=self.request.user)

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
