"""
apps/accounts/services.py

JA: 認証の業務ロジック。views から HTTP を切り離すための層。
    ここでは「与えられた資格情報が正しいか」を判定するだけ（純粋な処理）。
    セッションへの login()/logout() は Django のリクエストに依存するため views 側で行う。
    ＝ services は「判断」、views は「HTTP とセッションの副作用」を担当する分担。
VI: Logic nghiệp vụ xác thực. Tầng tách HTTP khỏi views.
    Ở đây chỉ xét "thông tin đăng nhập có đúng không" (xử lý thuần).
    login()/logout() vào session phụ thuộc request Django nên đặt ở views.
    Tức services lo "phán đoán", views lo "tác dụng phụ HTTP và session".
"""

from django.contrib.auth import authenticate

from apps.common.exceptions import ValidationError

from .models import User


def authenticate_user(*, username: str, password: str) -> User:
    """
    JA: 資格情報を検証し、正しければ User を返す。誤りならドメイン例外を投げる。
        HTTP ステータスへの変換は例外ハンドラが行うので、ここは HTTP を知らない。
    VI: Kiểm tra thông tin đăng nhập, đúng thì trả về User; sai thì ném exception nghiệp vụ.
        Việc đổi sang HTTP status do exception handler lo, nên ở đây không biết HTTP.
    """
    user = authenticate(username=username, password=password)
    if user is None:
        # JA: ユーザー名/パスワードのどちらが誤りかは明かさない（列挙攻撃対策）。
        # VI: Không tiết lộ sai username hay password (chống dò tài khoản).
        raise ValidationError(
            "ユーザー名またはパスワードが違います / Sai tên đăng nhập hoặc mật khẩu"
        )
    return user
