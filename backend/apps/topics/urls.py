"""
apps/topics/urls.py

JA: 学習木構造機能のルーティング登録。
VI: Đăng ký routing cho tính năng cây học tập.
"""

from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import KnowledgeNodeViewSet, LearningTreeView, TopicViewSet

router = DefaultRouter()
router.register("topics", TopicViewSet, basename="topic")
router.register("knowledge-nodes", KnowledgeNodeViewSet, basename="knowledge-node")

urlpatterns = [
    path("learning-tree/", LearningTreeView.as_view(), name="learning-tree"),
] + router.urls
