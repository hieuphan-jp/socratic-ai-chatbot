"""
apps/reviews/tests.py

JA: 復習スケジューリングの振る舞いを検証する。学習木の葉の見た目は
    「緑の濃さ=mastery_level(復習回数)」「復習の合図=is_due(予定日超過)」の
    2軸で決まるため、その2つが独立に動くことを重点的に確認する。
    ・完了を記録するたびに mastery_level が上がり、下がらないこと
    ・次回復習日が SM-2 の間隔(1日→6日→…)で伸びること
    ・予定日を過ぎた葉だけが is_due / due 一覧に出ること
    ・他人のスケジュールが見えないこと
    ※ チャット機能側のAPI(送信・完了ボタン)経由ではなく services を直接呼ぶ。
      チャットのAPI設計は別ブランチで変更中のため、そこに結合させない。
VI: Kiểm tra hành vi lập lịch ôn tập. Hình thức của lá trên cây học tập được
    quyết định bởi 2 trục: "độ đậm xanh = mastery_level (số lần ôn)" và
    "tín hiệu ôn tập = is_due (đã quá hạn)", nên tập trung kiểm tra 2 trục này
    hoạt động độc lập.
    - Mỗi lần ghi nhận hoàn thành thì mastery_level tăng và không giảm
    - Ngày ôn kế tiếp giãn ra theo SM-2 (1 ngày → 6 ngày → ...)
    - Chỉ lá đã quá hạn mới có is_due / xuất hiện ở danh sách due
    - Không thấy được lịch của người khác
    ※ Gọi thẳng services chứ không qua API của tính năng Chat (gửi tin/nút hoàn
      thành). Thiết kế API của Chat đang được sửa ở nhánh khác nên không ràng buộc vào đó.
"""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from apps.chat.models import Attempt, ChatSession
from apps.common.exceptions import ValidationError
from apps.topics.models import KnowledgeNode, Topic

from . import services
from .models import ReviewLog, ReviewSchedule

User = get_user_model()


def complete_once(session: ChatSession) -> Attempt:
    """
    JA: 「達成/復習完了ボタンを押した」1回分を作る。Attempt はチャット側が作る
        ものだが、reviews の入力として必要なのでテスト内で最小限を組み立てる。
    VI: Tạo 1 lượt "đã bấm nút hoàn thành". Attempt vốn do phía Chat tạo, nhưng là
        đầu vào của reviews nên ở test dựng tối thiểu.
    """
    attempt = Attempt.objects.create(chat_session=session, completed_at=timezone.now())
    services.record_review_result(attempt)
    return attempt


class ReviewScheduleServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="owner", password="pass12345")
        self.topic = Topic.objects.create(user=self.user, name="数学", position=0)
        self.node = KnowledgeNode.objects.create(
            topic=self.topic, title="一次方程式", content="x + 3 = 7"
        )
        self.session = ChatSession.objects.create(
            user=self.user, title="学習: 一次方程式", knowledge_node=self.node
        )

    def test_first_completion_creates_schedule_and_log(self):
        complete_once(self.session)

        schedule = ReviewSchedule.objects.get(node=self.node)
        self.assertEqual(schedule.learned_count, 1)
        self.assertEqual(schedule.mastery_level, 1)
        self.assertEqual(schedule.interval_days, 1)
        self.assertEqual(ReviewLog.objects.count(), 1)

    def test_interval_grows_with_repeated_reviews(self):
        # JA: SM-2 の既定間隔。1回目=1日、2回目=6日、3回目以降は係数倍で伸びる。
        # VI: Khoảng cách mặc định của SM-2: lần 1 = 1 ngày, lần 2 = 6 ngày, từ lần 3 nhân hệ số.
        complete_once(self.session)
        self.assertEqual(ReviewSchedule.objects.get(node=self.node).interval_days, 1)

        complete_once(self.session)
        self.assertEqual(ReviewSchedule.objects.get(node=self.node).interval_days, 6)

        complete_once(self.session)
        self.assertGreater(ReviewSchedule.objects.get(node=self.node).interval_days, 6)

    def test_mastery_level_only_increases_and_is_capped(self):
        for _ in range(ReviewSchedule.MASTERY_MAX_LEVEL + 3):
            complete_once(self.session)

        schedule = ReviewSchedule.objects.get(node=self.node)
        self.assertEqual(schedule.learned_count, ReviewSchedule.MASTERY_MAX_LEVEL + 3)
        self.assertEqual(schedule.mastery_level, ReviewSchedule.MASTERY_MAX_LEVEL)

    def test_is_due_is_independent_from_mastery_level(self):
        # JA: よく復習した(緑が濃い)葉でも、予定日を過ぎれば復習の合図は出る。
        # VI: Lá đã ôn nhiều (xanh đậm) nhưng quá hạn thì vẫn phải báo tới lượt ôn.
        complete_once(self.session)
        complete_once(self.session)
        schedule = ReviewSchedule.objects.get(node=self.node)
        self.assertEqual(schedule.mastery_level, 2)
        self.assertFalse(schedule.is_due)
        self.assertEqual(schedule.days_overdue, 0)

        schedule.next_review_at = timezone.now() - timedelta(days=3)
        schedule.save(update_fields=["next_review_at"])

        self.assertTrue(schedule.is_due)
        self.assertEqual(schedule.mastery_level, 2)
        self.assertEqual(schedule.days_overdue, 3)

    def test_completion_without_knowledge_node_is_rejected(self):
        # JA: 知識ノードが未作成のフリーチャットは、復習の対象にできない。
        # VI: Phiên chat tự do chưa tạo knowledge node thì không thể làm đối tượng ôn tập.
        free_session = ChatSession.objects.create(user=self.user, title="自由チャット")
        attempt = Attempt.objects.create(chat_session=free_session, completed_at=timezone.now())

        with self.assertRaises(ValidationError):
            services.record_review_result(attempt)


class ReviewScheduleApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="owner", password="pass12345")
        self.other = User.objects.create_user(username="stranger", password="pass12345")
        self.client.force_login(self.user)

        self.topic = Topic.objects.create(user=self.user, name="数学", position=0)
        self.learned = KnowledgeNode.objects.create(
            topic=self.topic, title="一次方程式", content="x + 3 = 7"
        )
        self.due_node = KnowledgeNode.objects.create(
            topic=self.topic, title="二次方程式", content="判別式"
        )
        self.session = ChatSession.objects.create(
            user=self.user, title="学習: 一次方程式", knowledge_node=self.learned
        )
        self.due_session = ChatSession.objects.create(
            user=self.user, title="学習: 二次方程式", knowledge_node=self.due_node
        )
        complete_once(self.session)
        complete_once(self.due_session)

        due_schedule = ReviewSchedule.objects.get(node=self.due_node)
        due_schedule.next_review_at = timezone.now() - timedelta(days=2)
        due_schedule.save(update_fields=["next_review_at"])

    def test_list_returns_material_to_paint_a_leaf(self):
        resp = self.client.get("/api/review-schedules/")
        self.assertEqual(resp.status_code, 200)

        entry = next(e for e in resp.json() if e["node_id"] == str(self.learned.id))
        self.assertEqual(entry["node_title"], "一次方程式")
        self.assertEqual(entry["topic_id"], str(self.topic.id))
        self.assertEqual(entry["mastery_level"], 1)
        self.assertEqual(entry["mastery_max_level"], ReviewSchedule.MASTERY_MAX_LEVEL)
        self.assertFalse(entry["is_due"])
        # JA: 葉から過去のチャットに戻れること(パターン2-3)。
        # VI: Từ chiếc lá quay lại được cuộc trò chuyện cũ (mẫu 2-3).
        self.assertEqual(entry["chat_session_id"], str(self.session.id))

    def test_due_endpoint_returns_only_overdue_nodes(self):
        resp = self.client.get("/api/review-schedules/due/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual([e["node_id"] for e in data], [str(self.due_node.id)])
        self.assertTrue(data[0]["is_due"])
        self.assertEqual(data[0]["days_overdue"], 2)

    def test_node_without_schedule_is_absent_from_list(self):
        # JA: 手動作成のノードは ReviewSchedule を持たない。一覧に出てこないので、
        #     フロントは「未学習(灰)」として塗る。
        # VI: Node tạo tay không có ReviewSchedule, không xuất hiện ở danh sách nên
        #     frontend tô là "chưa học (xám)".
        manual = KnowledgeNode.objects.create(topic=self.topic, title="手動", content="x")

        resp = self.client.get("/api/review-schedules/")
        node_ids = [e["node_id"] for e in resp.json()]
        self.assertNotIn(str(manual.id), node_ids)

    def test_other_user_sees_no_schedules(self):
        self.client.force_login(self.other)
        resp = self.client.get("/api/review-schedules/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), [])
