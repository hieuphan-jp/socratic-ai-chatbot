"""
apps/accounts/admin.py
JA: カスタム User を管理画面に登録する。Django 標準の UserAdmin を流用する。
VI: Đăng ký User tùy biến vào trang admin. Tái sử dụng UserAdmin chuẩn của Django.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User

admin.site.register(User, UserAdmin)
