"""
apps/accounts/tests.py

JA: 新規登録(POST /api/auth/signup/)を検証する。★発表デモでの同時利用向けに
    追加した機能なので、正常系・重複ユーザー名・弱いパスワードの3本を確認する。
VI: Kiểm tra đăng ký mới (POST /api/auth/signup/). ★Tính năng thêm để dùng đồng
    thời khi demo thuyết trình, nên kiểm tra 3 luồng: chính thường, trùng username,
    mật khẩu yếu.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase

User = get_user_model()


class SignupTests(TestCase):
    def test_signup_creates_user_and_logs_in(self):
        resp = self.client.post(
            "/api/auth/signup/",
            {"username": "attendee1", "password": "correct-horse-1"},
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.json()["username"], "attendee1")
        self.assertTrue(User.objects.filter(username="attendee1").exists())

        # JA: 登録直後にログイン状態(セッション)になっていることを確認する。
        # VI: Xác nhận ngay sau đăng ký đã ở trạng thái đăng nhập (session).
        me_resp = self.client.get("/api/auth/me/")
        self.assertEqual(me_resp.status_code, 200)
        self.assertEqual(me_resp.json()["username"], "attendee1")

    def test_signup_rejects_duplicate_username(self):
        User.objects.create_user(username="attendee2", password="correct-horse-1")

        resp = self.client.post(
            "/api/auth/signup/",
            {"username": "attendee2", "password": "another-pass-1"},
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)

    def test_signup_rejects_weak_password(self):
        resp = self.client.post(
            "/api/auth/signup/",
            {"username": "attendee3", "password": "1234"},
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertFalse(User.objects.filter(username="attendee3").exists())
