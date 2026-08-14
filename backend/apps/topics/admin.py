"""
JA: Django Adminへの登録。動作確認・手動でのデータ投入用。
    業務ロジックはここに書かない(services.pyの責務)。
VI: Đăng ký vào Django Admin. Dùng để kiểm tra hoạt động và nhập dữ liệu thủ công.
    Không viết logic nghiệp vụ ở đây (đó là trách nhiệm của services.py).
"""

from django.contrib import admin

from .models import KnowledgeNode, Topic


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ["name", "user", "parent", "position", "created_at"]
    list_filter = ["user"]
    search_fields = ["name", "description"]
    readonly_fields = ["id", "created_at", "updated_at"]
    ordering = ["user", "position", "created_at"]


@admin.register(KnowledgeNode)
class KnowledgeNodeAdmin(admin.ModelAdmin):
    list_display = ["title", "topic", "created_at"]
    list_filter = ["topic"]
    search_fields = ["title", "content"]
    readonly_fields = ["id", "created_at", "updated_at"]
    ordering = ["-created_at"]
