"""
apps/chat/tests.py

JA: 分岐推定(親ノードの確認)と、学習/復習の完了フローの検証。
    AIを呼ぶ経路はテスト対象にせず、DBとロジックだけを見る(APIクォータを使わない)。
    【統合2026-08-15】完了フローは develop の設計(Attempt + apps.reviews)に
    合わせてあるため、ChatSession に hint_count は無く Attempt 側に記録される。
VI: Kiểm tra tính năng đoán nhánh (xác nhận node cha) và luồng hoàn thành học/ôn tập.
    Không test đường đi gọi AI, chỉ xét DB và logic (không tốn quota API).
    【Tích hợp 2026-08-15】Luồng hoàn thành tuân theo thiết kế của develop
    (Attempt + apps.reviews), nên ChatSession không có hint_count mà ghi ở Attempt.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.chat import branching, services
from apps.chat.models import Attempt, ChatMessage, ChatSession
from apps.common.exceptions import NotFound, ValidationError
from apps.reviews.models import ReviewLog, ReviewSchedule
from apps.topics.models import KnowledgeNode, Topic

User = get_user_model()


class BranchingTestCase(TestCase):
    def setUp(self):
        # Tạo dữ liệu giả lập trong RAM
        self.user = User.objects.create_user(username="testuser", password="password")
        self.session = ChatSession.objects.create(user=self.user, title="Test Branch")
        self.msg1 = ChatMessage.objects.create(
            session=self.session, sender="USER", message_text="Bước 1"
        )
        self.msg2 = ChatMessage.objects.create(
            session=self.session, sender="USER", message_text="Bước 2"
        )

    def test_confirm_message_parent_success(self):
        # Chạy hàm service rẽ nhánh msg2 về msg1
        updated_msg = services.confirm_message_parent(
            session=self.session,
            message_id=self.msg2.id,
            parent_message_id=self.msg1.id,
        )

        # Kiểm tra dữ liệu thực tế lưu dưới DB
        self.assertEqual(updated_msg.parent_message.id, self.msg1.id)
        self.assertTrue(updated_msg.parent_confirmed)

    def test_confirm_message_parent_without_parent_keeps_confirmed(self):
        # JA: 「今のままにする」= 親を指定せずに確認だけ済ませるケース。
        # VI: "Giữ nguyên" = chỉ xác nhận mà không chỉ định node cha.
        updated_msg = services.confirm_message_parent(
            session=self.session, message_id=self.msg2.id, parent_message_id=None
        )
        self.assertIsNone(updated_msg.parent_message)
        self.assertTrue(updated_msg.parent_confirmed)

    def test_confirm_message_parent_rejects_unknown_message(self):
        with self.assertRaises(ValidationError):
            services.confirm_message_parent(
                session=self.session,
                message_id=self.msg1.id,
                parent_message_id="00000000-0000-0000-0000-000000000000",
            )


class SessionOwnershipTestCase(TestCase):
    """
    JA: 他人の KnowledgeNode に自分のセッションを紐付けられないこと(CONVENTIONS.md §10)。
    VI: Không được gắn session của mình vào KnowledgeNode của người khác (CONVENTIONS.md §10).
    """

    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="password")
        self.other = User.objects.create_user(username="other", password="password")
        topic = Topic.objects.create(user=self.owner, name="数学", position=0)
        self.node = KnowledgeNode.objects.create(topic=topic, title="一次方程式", content="x+3=7")

    def test_cannot_attach_session_to_other_users_node(self):
        with self.assertRaises(NotFound):
            services.create_chat_session_for_node(user=self.other, node_id=self.node.id)

    def test_owner_reuses_existing_session_for_node(self):
        first = services.create_chat_session_for_node(user=self.owner, node_id=self.node.id)
        second = services.create_chat_session_for_node(user=self.owner, node_id=self.node.id)
        self.assertEqual(first.id, second.id)


class CompletionFlowTestCase(TestCase):
    """
    JA: 完了ボタンを押したときに Attempt が1件でき、復習スケジュールが更新されること。
    VI: Khi bấm nút hoàn thành thì tạo 1 Attempt và cập nhật lịch ôn tập.
    """

    def setUp(self):
        self.user = User.objects.create_user(username="learner", password="password")
        self.topic = Topic.objects.create(user=self.user, name="数学", position=0)
        self.node = KnowledgeNode.objects.create(
            topic=self.topic, title="三平方", content="a^2+b^2"
        )
        self.session = ChatSession.objects.create(
            user=self.user, title="復習", knowledge_node=self.node
        )

    def test_complete_creates_attempt_and_review_records(self):
        services.send_message_and_get_ai_response(
            session=self.session, user_message_text="", action_type="COMPLETE", understood=True
        )

        self.assertEqual(Attempt.objects.filter(chat_session=self.session).count(), 1)
        attempt = Attempt.objects.get(chat_session=self.session)
        self.assertIsNotNone(attempt.completed_at)
        self.assertEqual(ReviewLog.objects.filter(attempt=attempt).count(), 1)
        self.assertEqual(ReviewSchedule.objects.filter(node=self.node).count(), 1)

    def test_complete_without_text_does_not_create_user_message(self):
        # JA: 本文なしで完了ボタンを押しても、ダミー発言が履歴に残らないこと。
        # VI: Bấm hoàn thành mà không nhập nội dung thì không để lại tin nhắn giả trong lịch sử.
        result = services.send_message_and_get_ai_response(
            session=self.session, user_message_text="", action_type="COMPLETE", understood=True
        )
        self.assertIsNone(result["user_message"])
        self.assertEqual(
            ChatMessage.objects.filter(
                session=self.session, sender=ChatMessage.Sender.USER
            ).count(),
            0,
        )

    def test_second_completion_creates_second_attempt(self):
        for _ in range(2):
            services.send_message_and_get_ai_response(
                session=self.session, user_message_text="", action_type="COMPLETE", understood=True
            )
        self.assertEqual(Attempt.objects.filter(chat_session=self.session).count(), 2)

    def test_free_chat_complete_requires_topic(self):
        # JA: knowledge_node未設定のセッションは、保存先Topicが無いと完了できない。
        # VI: Session chưa gắn knowledge_node thì không hoàn thành được nếu thiếu Topic để lưu.
        free_session = ChatSession.objects.create(user=self.user, title="自由チャット")
        with self.assertRaises(ValidationError):
            services.send_message_and_get_ai_response(
                session=free_session, user_message_text="", action_type="COMPLETE", understood=True
            )


class BigramBranchingTestCase(TestCase):
    """
    JA: 文字bigramによる分岐推定(AI不使用)の判定ロジック。
        「拾えること」より「誤って拾わないこと」を重点的に守る。誤検知は思考ツリーの
        形を黙って壊すが、検出漏れは単に直前の続きになるだけで害が小さいため。
    VI: Logic đoán nhánh bằng bigram ký tự (không dùng AI).
        Ưu tiên "không nhận nhầm" hơn là "bắt được hết". Nhận nhầm sẽ âm thầm làm hỏng
        hình dạng cây tư duy, còn bỏ sót chỉ khiến nó nối tiếp bước liền trước, ít hại hơn.
    """

    def test_detects_return_to_older_topic(self):
        suggestion = branching.suggest_parent(
            new_text="さっきの三平方の定理の証明も教えてください",
            candidates=[
                ("a", "三平方の定理について教えてください"),
                ("b", "直角三角形の斜辺はどう求めますか"),
                ("c", "円の面積の公式を知りたいです"),
            ],
        )
        self.assertIsNotNone(suggestion)
        self.assertEqual(suggestion.parent_id, "a")
        self.assertTrue(branching.should_adopt(suggestion))

    def test_natural_continuation_is_not_a_branch(self):
        suggestion = branching.suggest_parent(
            new_text="判別式が負のときはどうなりますか",
            candidates=[
                ("a", "二次方程式の解き方を教えてください"),
                ("b", "判別式とは何ですか"),
            ],
        )
        self.assertFalse(branching.should_adopt(suggestion))

    def test_polite_ending_alone_is_not_treated_as_similarity(self):
        # JA: 話題が全く違っても「〜てください」が共通なだけで分岐にしてはいけない。
        #     定型表現を除去する前は、この2文が score 0.15 に達して誤検知していた。
        # VI: Dù khác hẳn chủ đề, chỉ vì cùng đuôi "〜てください" thì không được coi là rẽ nhánh.
        #     Trước khi loại cụm cố định, 2 câu này đạt score 0.15 và bị nhận nhầm.
        suggestion = branching.suggest_parent(
            new_text="行列式の計算方法を教えてください",
            candidates=[
                ("a", "三平方の定理について教えてください"),
                ("b", "円の面積の公式を知りたいです"),
            ],
        )
        self.assertFalse(branching.should_adopt(suggestion))

    def test_shared_generic_word_stays_low_confidence(self):
        # JA: 「方程式」だけが共通の場合は候補には挙がっても採用しない。
        # VI: Nếu chỉ chung mỗi từ "phương trình" thì có thể thành ứng viên nhưng không được dùng.
        suggestion = branching.suggest_parent(
            new_text="連立方程式はどう解きますか",
            candidates=[
                ("a", "二次方程式の解き方を教えてください"),
                ("b", "一次方程式との違いは何ですか"),
            ],
        )
        self.assertFalse(branching.should_adopt(suggestion))

    def test_aizuchi_does_not_branch(self):
        suggestion = branching.suggest_parent(
            new_text="そうですね",
            candidates=[
                ("a", "微分の基本を教えてください"),
                ("b", "積分との関係は何ですか"),
            ],
        )
        self.assertFalse(branching.should_adopt(suggestion))

    def test_needs_at_least_two_candidates(self):
        # JA: 直前1件しかないなら「出戻り先」が存在しない。
        # VI: Chỉ có 1 ứng viên thì không tồn tại "bước cũ để quay lại".
        self.assertIsNone(
            branching.suggest_parent(new_text="続きを教えて", candidates=[("a", "微分の基本")])
        )

    def test_empty_text_is_safe(self):
        self.assertIsNone(
            branching.suggest_parent(new_text="", candidates=[("a", "微分"), ("b", "積分")])
        )
