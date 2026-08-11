"""
apps/common/models.py

JA: 全モデルが継承する抽象基底モデル。ここで「UUID 主キー」と「作成/更新時刻」を
    一元的に定義する。各アプリが個別に主キー方式を決めるとバラつくため、共通化する。
    abstract=True なので、このモデル自体はテーブルを持たない（継承先にだけ列が生える）。
VI: Model trừu tượng gốc mà mọi model kế thừa. Định nghĩa tập trung "khóa chính UUID"
    và "thời điểm tạo/cập nhật". Nếu mỗi app tự chọn kiểu khóa sẽ không đồng nhất nên
    gom về đây. Vì abstract=True, model này không có bảng (chỉ sinh cột ở lớp con).
"""

import uuid

from django.db import models


class BaseModel(models.Model):
    # JA: UUID 主キー。連番だと件数や他者の ID が推測できるため UUID を既定にする。
    # VI: Khóa chính UUID. Số tuần tự dễ đoán số lượng/ID người khác nên mặc định UUID.
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # JA: 作成・更新時刻は自動記録。監査やソートの土台になるため全モデルで持つ。
    # VI: Thời điểm tạo/cập nhật tự ghi. Là nền cho kiểm toán và sắp xếp nên mọi model đều có.
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        # JA: 既定では新しい順。個別アプリで上書きしてよい。
        # VI: Mặc định mới nhất trước. Từng app có thể ghi đè.
        ordering = ["-created_at"]
