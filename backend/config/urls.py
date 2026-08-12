"""
config/urls.py

JA: プロジェクト全体の URL 入口。各アプリの urls.py を api/ 配下に束ねるだけにする。
    ルーティングの実体は各アプリ側に置き、ここは「地図」に徹する（責務を薄く保つ）。
    新しいアプリを足すときは、ここに1行 include を追加する（手順は CONVENTIONS.md 参照）。
VI: Điểm vào URL của toàn dự án. Chỉ gom urls.py của từng app dưới tiền tố api/.
    Định tuyến thật nằm ở từng app; file này chỉ là "bản đồ" (giữ trách nhiệm mỏng).
    Khi thêm app mới, chèn 1 dòng include ở đây (xem hướng dẫn trong CONVENTIONS.md).
"""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    # JA: 認証系（ログイン等）。VI: Nhóm xác thực (đăng nhập...).
    path("api/auth/", include("apps.accounts.urls")),
    # JA: 各機能アプリの urls はここに1行ずつ include する（手順は CONVENTIONS.md §4）。
    # VI: urls của từng app tính năng include tại đây, mỗi app 1 dòng (xem CONVENTIONS.md §4).
    path("api/", include("apps.chat.urls")),
    path("api/", include("apps.topics.urls")),
]
