"""
apps/accounts/serializers.py

JA: 認証まわりの入出力スキーマ。serializer の責務は「JSON の形の定義と入力検証」まで。
    ログイン処理そのもの（認証）は services.py に置き、ここではデータ形だけを扱う。
VI: Lược đồ vào/ra của xác thực. Trách nhiệm của serializer chỉ tới "định nghĩa hình dạng
    JSON và kiểm tra đầu vào". Việc đăng nhập thật (xác thực) đặt ở services.py, ở đây chỉ
    lo hình dạng dữ liệu.
"""

from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    """JA: 現在ユーザーの公開表現。VI: Biểu diễn công khai của user hiện tại."""

    class Meta:
        model = User
        # JA: 返してよい最小限の項目のみ。パスワード等は絶対に含めない。
        # VI: Chỉ các trường tối thiểu được phép trả về. Tuyệt đối không có password...
        fields = ["id", "username", "email"]


class LoginSerializer(serializers.Serializer):
    """JA: ログイン入力の検証のみ。VI: Chỉ kiểm tra đầu vào đăng nhập."""

    username = serializers.CharField()
    password = serializers.CharField(write_only=True, style={"input_type": "password"})


class SignupSerializer(serializers.Serializer):
    """
    JA: 新規登録入力の検証のみ。ユーザー名の重複チェックやパスワード強度チェックは
        業務ロジックなので services.py 側で行う(ここは形の検証だけ)。
    VI: Chỉ kiểm tra hình dạng đầu vào đăng ký. Việc kiểm tra trùng username hay độ
        mạnh mật khẩu là logic nghiệp vụ nên đặt ở services.py (ở đây chỉ xét hình dạng).
    """

    username = serializers.CharField(min_length=3, max_length=150)
    password = serializers.CharField(write_only=True, style={"input_type": "password"})
