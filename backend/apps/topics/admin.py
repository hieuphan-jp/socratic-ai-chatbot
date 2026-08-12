"""
apps/topics/admin.py

JA: 管理画面からTopic/KnowledgeNodeを確認・追加できるようにする（動作確認用）。
VI: Cho phép xem/thêm Topic/KnowledgeNode từ trang quản trị (dùng để kiểm tra).
"""

from django.contrib import admin

from .models import KnowledgeNode, Topic


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ["name", "user", "parent", "position", "created_at"]
    list_filter = ["user"]
    search_fields = ["name"]


@admin.register(KnowledgeNode)
class KnowledgeNodeAdmin(admin.ModelAdmin):
    list_display = ["title", "topic", "origin_node", "created_at"]
    list_filter = ["topic__user"]
    search_fields = ["title", "content"]
