"""
apps/ai/apps.py
JA: ai アプリの登録情報。LLM プロバイダの抽象化層を提供する（DB モデルは持たない）。
VI: Thông tin đăng ký app ai. Cung cấp tầng trừu tượng nhà cung cấp LLM (không có model DB).
"""

from django.apps import AppConfig


class AiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.ai"
