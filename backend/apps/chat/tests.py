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

from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.chat import branching, services, steps
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

    def test_session_created_from_node_is_named_after_the_node(self):
        """
        JA: 【回帰】学習木から復習を始めたセッションがノード名で命名されること。
            views が未指定時に "New Chat Session" を渡していたため services の番兵
            ("New Session")と一致せず、全セッションが同名になりタイムログ上で
            見分けが付かなくなっていた(2026-08-16)。
        VI: 【Hồi quy】Phiên mở từ cây học tập phải được đặt tên theo tên node.
            Do views truyền "New Chat Session" khi không chỉ định nên không khớp
            sentinel ("New Session") của services, làm mọi phiên trùng tên và không
            phân biệt được trên nhật ký thời gian (2026-08-16).
        """
        session = services.create_chat_session_for_node(user=self.owner, node_id=self.node.id)
        self.assertEqual(session.title, "学習: 一次方程式")

    def test_explicit_title_is_kept(self):
        """JA: 明示指定した名前は上書きされない / VI: Tên chỉ định rõ không bị ghi đè"""
        session = services.create_chat_session_for_node(
            user=self.owner, node_id=self.node.id, title="復習1回目"
        )
        self.assertEqual(session.title, "復習1回目")

    def test_free_chat_without_node_uses_default_title(self):
        """JA: ノードに紐づかないフリーチャットは既定名 / VI: Chat tự do dùng tên mặc định"""
        session = services.create_chat_session_for_node(user=self.owner)
        self.assertEqual(session.title, services.DEFAULT_SESSION_TITLE)
        self.assertIsNone(session.knowledge_node_id)


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

    def test_free_chat_complete_renames_session_after_node(self):
        """
        JA: 【回帰】フリーチャット(node_id未指定で開始)を完了すると、生まれた
            KnowledgeNodeの名前でセッション名も更新されること。
            以前は knowledge_node の紐付けだけ行い title を放置していたため、
            タイムログ上でずっとフロントの既定名("New Chat Session")のままに
            なっていた(2026-08-16)。
        VI: 【Hồi quy】Hoàn thành 1 phiên chat tự do (bắt đầu không có node_id)
            phải đổi tên session theo tên KnowledgeNode vừa sinh ra.
            Trước đây chỉ gắn knowledge_node mà bỏ mặc title, nên trên nhật ký
            thời gian mãi mãi giữ tên mặc định của frontend ("New Chat Session")
            (2026-08-16).
        """
        free_session = services.create_chat_session_for_node(user=self.user)
        self.assertEqual(free_session.title, services.DEFAULT_SESSION_TITLE)

        services.send_message_and_get_ai_response(
            session=free_session,
            user_message_text="",
            action_type="COMPLETE",
            understood=True,
            topic_id=self.topic.id,
        )

        free_session.refresh_from_db()
        self.assertIsNotNone(free_session.knowledge_node)
        self.assertEqual(free_session.title, f"学習: {free_session.knowledge_node.title}")

    def test_free_chat_first_message_names_session_even_if_never_completed(self):
        """
        JA: 【回帰】完了ボタンを一度も押さずに終わったフリーチャットでも、最初の
            メッセージを送った時点でセッション名が既定名("New Chat Session")から
            変わること。以前は完了時にしか改名しなかったため、途中で終わった
            セッションはタイムログ上でずっと既定名のままだった(2026-08-16)。
        VI: 【Hồi quy】Chat tự do dù chưa từng bấm hoàn thành, vẫn phải đổi tên
            session ngay khi gửi tin nhắn đầu tiên (khỏi tên mặc định "New Chat
            Session"). Trước đây chỉ đổi tên lúc hoàn thành, nên session bỏ dở
            giữa chừng mãi mãi giữ tên mặc định trên nhật ký thời gian (2026-08-16).
        """
        free_session = services.create_chat_session_for_node(user=self.user)

        services.send_message_and_get_ai_response(
            session=free_session,
            user_message_text="二分探索のアルゴリズムについて教えてください",
            action_type="ANSWER",
        )

        free_session.refresh_from_db()
        self.assertIsNone(free_session.knowledge_node)
        self.assertNotEqual(free_session.title, services.DEFAULT_SESSION_TITLE)
        self.assertEqual(free_session.title, "二分探索のアルゴリズムについて教えてください")

    def test_second_message_does_not_rename_already_named_session(self):
        """JA: 2件目以降の発言では改名しない(最初の1件だけの規則) / VI: Không đổi tên từ tin nhắn thứ 2 trở đi"""
        free_session = services.create_chat_session_for_node(user=self.user)
        services.send_message_and_get_ai_response(
            session=free_session, user_message_text="最初の質問です", action_type="ANSWER"
        )
        free_session.refresh_from_db()
        first_title = free_session.title

        services.send_message_and_get_ai_response(
            session=free_session, user_message_text="2つ目の質問です", action_type="ANSWER"
        )
        free_session.refresh_from_db()
        self.assertEqual(free_session.title, first_title)

    def test_db_rejects_second_active_attempt_for_same_session(self):
        """
        JA: 【回帰】完了ボタンの二重押下対策の土台となるDB制約そのものを検証する。
            1セッションにつき「未完了(completed_at IS NULL)」のAttemptは同時に
            1件までしか存在できないこと。
        VI: 【Hồi quy】Kiểm tra trực tiếp ràng buộc DB làm nền tảng cho việc chống
            bấm nút hoàn thành 2 lần. Mỗi session chỉ được có tối đa 1 Attempt
            "chưa hoàn thành" (completed_at IS NULL) tại một thời điểm.
        """
        Attempt.objects.create(chat_session=self.session)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Attempt.objects.create(chat_session=self.session)

    def test_double_complete_free_chat_discards_orphan_node(self):
        """
        JA: 【回帰】学習完了ボタンの二重押下(2つのリクエストがほぼ同時に、まだ
            knowledge_nodeが紐付いていない古いsessionの状態を見た状況)を、
            同じDB行を独立に読んだ2つのPythonオブジェクトで再現する。
            2回目は自分が作ったノードを孤立させず破棄し、1回目が作った
            ノードをそのまま返すこと(=知識ノードが重複しない)。
        VI: 【Hồi quy】Mô phỏng bấm nút hoàn thành học 2 lần liên tiếp (2 request
            gần như đồng thời, cùng thấy session chưa gắn knowledge_node) bằng
            2 đối tượng Python đọc độc lập cùng 1 dòng DB. Lần gọi thứ 2 phải tự
            hủy node mình vừa tạo (không để mồ côi) và trả về node mà lần gọi
            thứ nhất đã tạo (không bị nhân đôi knowledge node).
        """
        free_session = services.create_chat_session_for_node(user=self.user)
        # JA: 2つの「リクエスト」がそれぞれ独立に取得したsessionを模す。
        #     どちらも knowledge_node=None の古い状態のまま。
        # VI: Mô phỏng 2 "request" mỗi bên tự lấy session độc lập.
        #     Cả 2 đều đang giữ trạng thái cũ knowledge_node=None.
        request_a_session = ChatSession.objects.get(id=free_session.id)
        request_b_session = ChatSession.objects.get(id=free_session.id)

        winner_node = services.create_knowledge_node_from_session(
            session=request_a_session, user=self.user, topic_id=self.topic.id
        )
        result_node = services.create_knowledge_node_from_session(
            session=request_b_session, user=self.user, topic_id=self.topic.id
        )

        self.assertEqual(result_node.id, winner_node.id)
        # JA: setUpで作った self.node ("三平方") とは別に、この free_session からは
        #     ちょうど1件だけ知識ノードが生まれていること(=孤立ノードが残っていない)。
        # VI: Ngoài self.node ("三平方") tạo ở setUp, từ free_session này phải sinh ra
        #     đúng 1 knowledge node (không còn node mồ côi nào sót lại).
        self.assertEqual(
            KnowledgeNode.objects.filter(topic=self.topic).exclude(id=self.node.id).count(), 1
        )
        free_session.refresh_from_db()
        self.assertEqual(free_session.knowledge_node_id, winner_node.id)

    def test_claim_attempt_for_action_grants_completion_to_only_one_caller(self):
        """
        JA: 【回帰】2つのリクエストが同じ未完了Attemptに合流した状況
            (get_or_create_active_attemptが同じAttemptを返すケース)を再現し、
            claim_attempt_for_actionの「完了権」(won_completion)が片方にしか
            与えられないこと。send_message_and_get_ai_response側はこのフラグを
            見てからでないとSM-2(record_review_result)を呼ばないため、これが
            成り立てば二重適用は起きない。
        VI: 【Hồi quy】Mô phỏng 2 request cùng hội tụ về 1 Attempt chưa hoàn thành
            (trường hợp get_or_create_active_attempt trả về cùng 1 Attempt), và
            kiểm tra "quyền hoàn thành" (won_completion) của claim_attempt_for_action
            chỉ được cấp cho đúng 1 trong 2. send_message_and_get_ai_response chỉ gọi
            SM-2 (record_review_result) khi cờ này đúng, nên nếu điều này đúng thì
            không có chuyện áp dụng 2 lần.
        """
        attempt = Attempt.objects.create(chat_session=self.session)

        with patch.object(services, "get_or_create_active_attempt", return_value=attempt):
            _, won_first = services.claim_attempt_for_action(
                session=self.session, action_type="COMPLETE"
            )
            _, won_second = services.claim_attempt_for_action(
                session=self.session, action_type="COMPLETE"
            )

        self.assertTrue(won_first)
        self.assertFalse(won_second)
        attempt.refresh_from_db()
        self.assertIsNotNone(attempt.completed_at)

    def test_won_completion_gate_prevents_double_sm2_end_to_end(self):
        """
        JA: 【回帰】send_message_and_get_ai_responseを通しで呼び、claim_attempt_for_action
            が返すwon_completionがFalseの時にrecord_review_resultが呼ばれない
            (=ReviewLogが増えない)ことをエンドツーエンドで確認する。
        VI: 【Hồi quy】Gọi xuyên suốt send_message_and_get_ai_response, xác nhận
            record_review_result KHÔNG được gọi (ReviewLog không tăng) khi
            claim_attempt_for_action trả về won_completion=False.
        """
        attempt = Attempt.objects.create(chat_session=self.session)

        with patch.object(services, "claim_attempt_for_action", return_value=(attempt, False)):
            services.send_message_and_get_ai_response(
                session=self.session, user_message_text="", action_type="COMPLETE", understood=True
            )

        self.assertEqual(ReviewLog.objects.filter(attempt=attempt).count(), 0)


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


class StepClassificationTestCase(TestCase):
    """
    JA: 相槌の足切りと、幹/枝の番号採番(1, 2, 3, 3-1)の検証。どちらもAIを使わない純ロジック。
    VI: Kiểm tra việc lọc câu đệm và đánh số thân/nhánh (1, 2, 3, 3-1). Đều là logic thuần, không dùng AI.
    """

    def test_aizuchi_is_trivial(self):
        for text in ["そうですね", "なるほど", "はい", "OK", "ありがとうございます", "vâng"]:
            self.assertTrue(steps.is_trivial_message(text), text)

    def test_real_question_is_not_trivial(self):
        for text in [
            "HTMLの役割について教えてください",
            "なぜ判別式が必要なの？",
            "そうですね、では次にCSSについて教えて",
        ]:
            self.assertFalse(steps.is_trivial_message(text), text)

    def test_short_question_with_question_mark_is_kept(self):
        # JA: 短くても疑問符があれば質問として扱う。
        # VI: Ngắn nhưng có dấu hỏi thì vẫn coi là câu hỏi.
        self.assertFalse(steps.is_trivial_message("なぜ?"))

    def test_step_labels_number_trunk_and_branches(self):
        user = User.objects.create_user(username="labels", password="password")
        session = ChatSession.objects.create(user=user, title="t")
        Kind = ChatMessage.StepKind

        s1 = ChatMessage.objects.create(
            session=session, sender="USER", message_text="1", step_kind=Kind.TRUNK
        )
        s2 = ChatMessage.objects.create(
            session=session, sender="USER", message_text="2", step_kind=Kind.TRUNK
        )
        b1 = ChatMessage.objects.create(
            session=session,
            sender="USER",
            message_text="2の枝",
            step_kind=Kind.BRANCH,
            parent_message=s2,
        )
        b2 = ChatMessage.objects.create(
            session=session,
            sender="USER",
            message_text="2の枝その2",
            step_kind=Kind.BRANCH,
            parent_message=s2,
        )
        nested = ChatMessage.objects.create(
            session=session,
            sender="USER",
            message_text="枝の枝",
            step_kind=Kind.BRANCH,
            parent_message=b1,
        )
        s3 = ChatMessage.objects.create(
            session=session, sender="USER", message_text="3", step_kind=Kind.TRUNK
        )

        labels = steps.build_step_labels([s1, s2, b1, b2, nested, s3])
        self.assertEqual(labels[s1.id], "1")
        self.assertEqual(labels[s2.id], "2")
        self.assertEqual(labels[b1.id], "2-1")
        self.assertEqual(labels[b2.id], "2-2")
        self.assertEqual(labels[nested.id], "2-1-1")
        # JA: ★枝が挟まっても幹の番号は連番のまま(以前はここが時系列の通し番号でズレていた)。
        # VI: ★Dù có nhánh xen giữa, số của thân vẫn liên tiếp (trước đây đánh số theo thời gian nên lệch).
        self.assertEqual(labels[s3.id], "3")

    def test_graph_excludes_non_step_messages(self):
        user = User.objects.create_user(username="graph", password="password")
        session = ChatSession.objects.create(user=user, title="t")
        trunk = ChatMessage.objects.create(
            session=session,
            sender="USER",
            message_text="HTMLとは",
            step_kind=ChatMessage.StepKind.TRUNK,
            step_title="HTMLとは",
        )
        # JA: 相槌とAIの返答は木に出ない。 VI: Câu đệm và câu trả lời AI không lên cây.
        ChatMessage.objects.create(session=session, sender="USER", message_text="そうですね")
        ChatMessage.objects.create(session=session, sender="AI", message_text="いい質問です")

        graph = services.get_session_graph_data(session=session)
        self.assertEqual([n["id"] for n in graph["nodes"]], [str(trunk.id)])
        self.assertEqual(graph["nodes"][0]["data"]["step_label"], "1")
        self.assertEqual(graph["nodes"][0]["data"]["title"], "HTMLとは")

    def test_fallback_title_strips_question_tail(self):
        self.assertEqual(steps.fallback_title("HTMLの役割について教えてください"), "HTMLの役割")
        self.assertEqual(steps.fallback_title("二次方程式とは何ですか？"), "二次方程式")
