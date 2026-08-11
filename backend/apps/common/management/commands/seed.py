"""
apps/common/management/commands/seed.py

JA: ダミーデータ投入コマンド。clone 直後の全員が同じ初期状態で開発を始められるようにする。
    現状はデモユーザー1人（demo / demo12345）を作るだけ。冪等（何度実行しても増殖しない）。
    各機能アプリが追加されたら、担当がこのコマンドに自分のダミーデータ生成を追記してよい。
    実行: python manage.py seed
    共通の入口なので common アプリに置く（特定機能に依存しない土台のため）。
VI: Lệnh nạp dữ liệu mẫu. Giúp mọi người sau khi clone bắt đầu với cùng trạng thái ban đầu.
    Hiện chỉ tạo 1 user demo (demo / demo12345). Idempotent (chạy nhiều lần không nhân bản).
    Khi có app tính năng mới, người phụ trách có thể thêm phần tạo dữ liệu mẫu của mình vào đây.
    Chạy: python manage.py seed
    Là cửa dùng chung nên đặt ở app common (nền tảng, không phụ thuộc chức năng cụ thể).
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

User = get_user_model()

DEMO_USERNAME = "demo"
DEMO_PASSWORD = "demo12345"  # noqa: S105  JA: 開発用の固定値 / VI: giá trị cố định cho dev


class Command(BaseCommand):
    help = "開発用のダミーデータを投入する / Nạp dữ liệu mẫu cho phát triển"

    @transaction.atomic
    def handle(self, *args, **options):
        # JA: get_or_create で冪等に。既存なら作り直さない。
        # VI: get_or_create để idempotent. Đã có thì không tạo lại.
        user, created = User.objects.get_or_create(username=DEMO_USERNAME)
        if created:
            user.set_password(DEMO_PASSWORD)
            user.save()
            self.stdout.write(
                self.style.SUCCESS(f"created user: {DEMO_USERNAME} / {DEMO_PASSWORD}")
            )
        else:
            self.stdout.write(f"user already exists: {DEMO_USERNAME}")

        self.stdout.write(self.style.SUCCESS("seed done / hoàn tất"))
