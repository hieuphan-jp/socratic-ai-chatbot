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
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError

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


def register_user(*, username: str, password: str) -> User:
    """
    JA: ★発表デモでの同時利用向け。聴衆が各自このAPIで自分のアカウントを作り、
        学習内容ツリー・チャット履歴を他の参加者と分けて使えるようにする
        (demo/demo12345の単一共有アカウントだと全員のデータが混ざるため追加した)。
        ユーザー名の重複とパスワード強度(base.pyのAUTH_PASSWORD_VALIDATORS)を
        ここで検証し、問題なければ User を作成して返す。
    VI: ★Dùng cho việc nhiều người dùng đồng thời khi demo thuyết trình. Mỗi khán giả
        tự tạo tài khoản qua API này để tách riêng cây nội dung đã học và lịch sử chat
        với người khác (thêm vì tài khoản demo/demo12345 dùng chung sẽ làm dữ liệu của
        tất cả mọi người bị trộn lẫn). Kiểm tra trùng username và độ mạnh mật khẩu
        (AUTH_PASSWORD_VALIDATORS ở base.py) ở đây; hợp lệ thì tạo User rồi trả về.
    """
    if User.objects.filter(username=username).exists():
        raise ValidationError(
            "このユーザー名は既に使われています / Tên đăng nhập này đã được sử dụng"
        )
    try:
        validate_password(password)
    except DjangoValidationError as e:
        raise ValidationError(" / ".join(e.messages)) from e
    return User.objects.create_user(username=username, password=password)
