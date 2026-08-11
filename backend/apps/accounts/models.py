"""
apps/accounts/models.py

JA: カスタム User モデル。Django では User を後から差し替えるのが極めて困難なため、
    プロジェクト初期に AbstractUser を継承した独自 User を用意しておく（拡張の受け皿）。
    ★ここでは要件どおりフィールドを一切足さない。将来 DB 担当が氏名や役割などを
    自由に追加できるようにするための「空の器」。この方針は勝手に破らないこと。
VI: Model User tùy biến. Trong Django, thay User về sau rất khó, nên ngay từ đầu ta tạo
    User riêng kế thừa AbstractUser (chỗ để mở rộng).
    ★Theo yêu cầu, KHÔNG thêm bất kỳ trường nào ở đây. Đây là "chiếc hộp rỗng" để sau này
    người phụ trách DB tự thêm họ tên, vai trò... Không được tự ý phá vỡ nguyên tắc này.
"""

from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    # JA: 追加フィールドはあえて置かない（AbstractUser の username/password/email 等で十分）。
    # VI: Cố ý không thêm trường (username/password/email... của AbstractUser là đủ).
    pass
