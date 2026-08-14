# Create your tests here.
# JA: 分岐機能の単体テスト (API quotaを消費せずにDBとロジックを検証)
# VI: Unit Test tính năng rẽ nhánh (Kiểm tra DB & logic không tốn API quota)

from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.chat.models import ChatSession, ChatMessage
from apps.chat import services

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