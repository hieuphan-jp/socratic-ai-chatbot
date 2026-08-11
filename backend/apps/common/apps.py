"""
apps/common/apps.py
JA: common アプリの登録情報。全アプリが共有する基盤（基底モデル・例外・権限）を提供する。
VI: Thông tin đăng ký app common. Cung cấp nền tảng dùng chung (base model, exception, quyền).
"""

from django.apps import AppConfig


class CommonConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.common"
