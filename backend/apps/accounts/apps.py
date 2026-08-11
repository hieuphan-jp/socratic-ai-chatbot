"""
apps/accounts/apps.py
JA: accounts アプリの登録情報。カスタム User と認証 API を担当する。
VI: Thông tin đăng ký app accounts. Phụ trách User tùy biến và API xác thực.
"""

from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accounts"
