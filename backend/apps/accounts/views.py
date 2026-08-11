"""
apps/accounts/views.py

JA: 認証 API。views の責務は「認可・入力検証・services 呼び出し・シリアライズ」の4つだけ。
    業務ロジック（資格情報の判定）は services.py に置く。ここではセッションへの
    login()/logout() という Django 依存の副作用と、CSRF Cookie 発行を担当する。
VI: API xác thực. Trách nhiệm của views chỉ 4 việc: "phân quyền, kiểm tra đầu vào,
    gọi services, tuần tự hóa". Logic nghiệp vụ (xét thông tin đăng nhập) ở services.py.
    Ở đây lo tác dụng phụ phụ thuộc Django là login()/logout() vào session và phát CSRF Cookie.
"""

from django.contrib.auth import login, logout
from django.middleware.csrf import get_token
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from . import services
from .serializers import LoginSerializer, UserSerializer


class CsrfView(APIView):
    """
    JA: フロントが最初に叩き、CSRF Cookie を受け取るための入口。
        SPA はテンプレート経由で token を埋め込めないため、明示的に配布する。
    VI: Điểm frontend gọi đầu tiên để nhận CSRF Cookie.
        SPA không nhúng token qua template nên phải phát token một cách tường minh.
    """

    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"csrfToken": get_token(request)})


class LoginView(APIView):
    """JA: ログイン。未認証でも叩けるよう AllowAny。VI: Đăng nhập; AllowAny để chưa auth vẫn gọi được."""

    permission_classes = [AllowAny]

    def post(self, request):
        # 1) JA: 入力検証（serializer） / VI: Kiểm tra đầu vào (serializer)
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # 2) JA: 業務ロジックは services へ委譲 / VI: Ủy thác logic cho services
        user = services.authenticate_user(**serializer.validated_data)

        # 3) JA: セッション開始（Django 依存の副作用）/ VI: Bắt đầu session (tác dụng phụ phụ thuộc Django)
        login(request, user)

        # 4) JA: シリアライズして返す / VI: Tuần tự hóa rồi trả về
        return Response(UserSerializer(user).data)


class LogoutView(APIView):
    """JA: ログアウト。VI: Đăng xuất."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    """JA: 現在ユーザーの取得。フロントの認証ガードに使う。VI: Lấy user hiện tại; dùng cho auth guard ở frontend."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)
