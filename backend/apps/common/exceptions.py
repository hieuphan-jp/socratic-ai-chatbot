"""
apps/common/exceptions.py

JA: 業務ロジック層(services.py)が投げる共通例外と、DRF 例外ハンドラをまとめる。
    services は HTTP を知らない純粋な処理にしたい。そこで services は下記の
    ドメイン例外を投げ、views/DRF がそれを HTTP ステータスへ翻訳する。
    こうすると Django 未経験者でも「HTTP を意識せず」ロジックを書ける。
VI: Gom các exception dùng chung mà tầng nghiệp vụ (services.py) ném ra, và bộ xử lý
    exception của DRF. Ta muốn services là xử lý thuần, không biết HTTP. Vì vậy services
    ném exception nghiệp vụ bên dưới, còn views/DRF dịch chúng sang HTTP status.
    Nhờ đó người chưa quen Django vẫn viết được logic mà "không cần nghĩ tới HTTP".
"""

from rest_framework import status
from rest_framework.views import exception_handler as drf_default_handler


class DomainError(Exception):
    """
    JA: 業務ルール違反を表す基底例外。services 層はこれ（の派生）を投げる。
    VI: Exception gốc biểu thị vi phạm quy tắc nghiệp vụ. Tầng services ném (lớp con của) nó.
    """

    # JA: 既定の HTTP ステータス。派生クラスで上書きする。
    # VI: HTTP status mặc định. Lớp con ghi đè.
    status_code = status.HTTP_400_BAD_REQUEST
    default_message = "リクエストを処理できません / Không thể xử lý yêu cầu"

    def __init__(self, message: str | None = None):
        self.message = message or self.default_message
        super().__init__(self.message)


class ValidationError(DomainError):
    """JA: 入力値が不正。VI: Giá trị đầu vào không hợp lệ."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_message = "入力値が不正です / Dữ liệu đầu vào không hợp lệ"


class PermissionDenied(DomainError):
    """JA: 権限なし。VI: Không có quyền."""

    status_code = status.HTTP_403_FORBIDDEN
    default_message = "権限がありません / Không có quyền"


class NotFound(DomainError):
    """JA: 対象が存在しない。VI: Không tìm thấy đối tượng."""

    status_code = status.HTTP_404_NOT_FOUND
    default_message = "見つかりません / Không tìm thấy"


def drf_exception_handler(exc, context):
    """
    JA: DRF の共通例外ハンドラ。まず DomainError を HTTP レスポンスへ翻訳し、
        それ以外は DRF 標準の処理に委譲する。settings の EXCEPTION_HANDLER で登録。
    VI: Bộ xử lý exception chung của DRF. Trước tiên dịch DomainError sang HTTP response,
        phần còn lại giao cho xử lý mặc định của DRF. Đăng ký ở EXCEPTION_HANDLER trong settings.
    """
    if isinstance(exc, DomainError):
        from rest_framework.response import Response

        return Response({"detail": exc.message}, status=exc.status_code)
    return drf_default_handler(exc, context)
