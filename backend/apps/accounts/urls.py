"""
apps/accounts/urls.py
JA: 認証エンドポイントの定義。config/urls.py で api/auth/ 配下にマウントされる。
    -> /api/auth/csrf/  /api/auth/login/  /api/auth/logout/  /api/auth/me/  /api/auth/signup/
VI: Định nghĩa endpoint xác thực. Được gắn dưới api/auth/ tại config/urls.py.
"""

from django.urls import path

from .views import CsrfView, LoginView, LogoutView, MeView, SignupView

urlpatterns = [
    path("csrf/", CsrfView.as_view(), name="csrf"),
    path("login/", LoginView.as_view(), name="login"),
    path("signup/", SignupView.as_view(), name="signup"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("me/", MeView.as_view(), name="me"),
]
