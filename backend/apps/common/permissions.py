"""
apps/common/permissions.py

JA: 「所有者だけがそのオブジェクトを操作できる」を表す共通権限クラス。
    多くのアプリで「自分のデータしか触れない」要件が出るため共通化する。
    オブジェクトの .user が request.user と一致するかで判定する。
VI: Lớp quyền dùng chung nghĩa là "chỉ chủ sở hữu mới thao tác được đối tượng".
    Nhiều app cần "chỉ chạm dữ liệu của mình" nên gom về đây.
    Xét bằng cách so .user của đối tượng với request.user.
"""

from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    """
    JA: object 単位の権限。ViewSet の get_queryset で user 絞り込みをするのが第一防御線、
        本クラスは詳細操作(取得/更新/削除)での二重の安全確認として使う。
    VI: Quyền ở mức object. Lọc theo user trong get_queryset của ViewSet là tuyến phòng thủ
        đầu tiên; lớp này dùng như lớp kiểm tra thứ hai khi thao tác chi tiết (đọc/sửa/xóa).
    """

    def has_object_permission(self, request, view, obj):
        # JA: 対象が .user を持つ前提。所有者判定を一箇所に閉じ込める。
        # VI: Giả định đối tượng có .user. Gói việc xác định chủ sở hữu vào một chỗ.
        return getattr(obj, "user_id", None) == request.user.id
