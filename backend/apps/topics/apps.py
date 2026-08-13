"""
apps/topics/apps.py
JA: topics アプリの登録情報。学習木構造（Topic/KnowledgeNode）を担当する。
VI: Thông tin đăng ký app topics. Phụ trách cấu trúc cây học tập (Topic/KnowledgeNode).
"""

from django.apps import AppConfig


class TopicsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.topics"
