"""
apps/common/management/commands/seed.py

JA: ダミーデータ投入コマンド。clone 直後の全員が同じ初期状態で開発を始められるようにする。
    デモユーザー1人（demo / demo12345）に加え、学習木構造画面(学習内容ツリー)を実データで
    確認できるよう、トピック階層・定着度の異なる知識ノード・復習スケジュールも投入する。
    冪等（何度実行しても増殖しない）。
    各機能アプリが追加されたら、担当がこのコマンドに自分のダミーデータ生成を追記してよい。
    実行: python manage.py seed
    共通の入口なので common アプリに置く（特定機能に依存しない土台のため）。
VI: Lệnh nạp dữ liệu mẫu. Giúp mọi người sau khi clone bắt đầu với cùng trạng thái ban đầu.
    Ngoài 1 user demo (demo / demo12345), còn nạp cả phân cấp Topic, KnowledgeNode với độ
    ghi nhớ khác nhau, và ReviewSchedule, để có thể xem màn hình cây học tập với dữ liệu thật.
    Idempotent (chạy nhiều lần không nhân bản).
    Khi có app tính năng mới, người phụ trách có thể thêm phần tạo dữ liệu mẫu của mình vào đây.
    Chạy: python manage.py seed
    Là cửa dùng chung nên đặt ở app common (nền tảng, không phụ thuộc chức năng cụ thể).
"""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

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

        self._seed_learning_tree(user)

        self.stdout.write(self.style.SUCCESS("seed done / hoàn tất"))

    def _seed_learning_tree(self, user) -> None:
        """
        JA: 学習木構造画面を実データで確認するためのトピック・知識ノード・復習
            スケジュールを投入する。色分け(mastery_level)・復習タイミング(is_due)・
            未学習(スケジュール無し)の3パターンが揃うようにする。
        VI: Nạp Topic/KnowledgeNode/ReviewSchedule để xem màn hình cây học tập với
            dữ liệu thật. Đảm bảo có đủ 3 kiểu: đã tô màu (mastery_level), tới hạn
            ôn tập (is_due), và chưa học (không có schedule).
        """
        from apps.reviews.models import ReviewSchedule
        from apps.topics.models import KnowledgeNode, Topic

        if Topic.objects.filter(user=user).exists():
            self.stdout.write("learning tree already seeded")
            return

        math = Topic.objects.create(user=user, name="数学", position=0)
        algebra = Topic.objects.create(user=user, name="代数", parent=math, position=0)
        geometry = Topic.objects.create(user=user, name="幾何", parent=math, position=1)
        programming = Topic.objects.create(user=user, name="プログラミング", position=1)

        now = timezone.now()

        def add_node(
            *, topic: Topic, title: str, content: str, mastery: int, overdue_days: int | None
        ):
            """
            JA: mastery=0 は「未学習」を表し、ReviewSchedule を作らない
                (=手動作成ノードと同じ状態)。overdue_days>0 なら期限超過、
                0 ならちょうど期限、None なら期限前。
            VI: mastery=0 nghĩa là "chưa học", không tạo ReviewSchedule
                (giống node tạo tay). overdue_days>0 là quá hạn, 0 là vừa
                tới hạn, None là chưa tới hạn.
            """
            node = KnowledgeNode.objects.create(topic=topic, title=title, content=content)
            if mastery == 0:
                return
            next_review_at = (
                now - timedelta(days=overdue_days)
                if overdue_days is not None
                else now + timedelta(days=3)
            )
            ReviewSchedule.objects.create(
                node=node,
                interval_days=3,
                repetitions=mastery,
                learned_count=mastery,
                next_review_at=next_review_at,
                last_learned_at=now - timedelta(days=1),
            )

        add_node(
            topic=algebra,
            title="一次方程式の基礎",
            content="x + 3 = 7 のような一次方程式の解き方。",
            mastery=5,
            overdue_days=None,
        )
        add_node(
            topic=algebra,
            title="二次方程式と判別式",
            content="判別式 D = b^2 - 4ac の符号で解の個数が決まる。",
            mastery=2,
            overdue_days=None,
        )
        add_node(
            topic=algebra,
            title="因数分解",
            content="たすき掛けを使った因数分解の手順。",
            mastery=3,
            overdue_days=2,
        )
        add_node(
            topic=geometry,
            title="三平方の定理",
            content="直角三角形の3辺の関係 a^2 + b^2 = c^2。",
            mastery=1,
            overdue_days=7,
        )
        add_node(
            topic=geometry,
            title="円周角の定理",
            content="同じ弧に対する円周角はすべて等しい。",
            mastery=0,
            overdue_days=None,
        )
        add_node(
            topic=programming,
            title="クイックソート",
            content="分割統治法によるソートアルゴリズム。平均計算量 O(n log n)。",
            mastery=4,
            overdue_days=None,
        )

        self.stdout.write(self.style.SUCCESS("seeded learning tree (topics/nodes/schedules)"))
