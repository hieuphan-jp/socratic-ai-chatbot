"""
apps/ai/tests.py

JA: GeminiProviderが「system役割を system_instruction へ」「user/assistantの履歴を
    複数ターンのcontentsへ」正しく変換することを検証する。以前は messages の最後の
    1件しかGeminiへ送っておらず、システムプロンプトと会話履歴が丸ごと無視される
    バグがあった(AI_PROVIDER=fakeでの開発中は表面化しなかった)。
    実際のGemini APIは呼ばない。genai.list_models/GenerativeModelをモックし、
    ロジックだけを検証する。
VI: Kiểm tra GeminiProvider chuyển đúng "tin nhắn role system vào system_instruction"
    và "lịch sử user/assistant thành contents nhiều lượt". Trước đây chỉ gửi đúng 1 tin
    nhắn cuối cùng của messages cho Gemini, bỏ qua toàn bộ system prompt và lịch sử hội
    thoại (không lộ ra khi phát triển với AI_PROVIDER=fake).
    Không gọi API Gemini thật. Mock genai.list_models/GenerativeModel, chỉ kiểm tra logic.
"""

from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from apps.ai.base import ChatMessage
from apps.ai.fake import FakeProvider


def _fake_model_list():
    m = MagicMock()
    m.name = "models/gemini-3.5-flash"
    m.supported_generation_methods = ["generateContent"]
    return [m]


class GeminiProviderTests(SimpleTestCase):
    def _make_provider(self):
        from apps.ai.gemini import GeminiProvider

        with (
            patch("apps.ai.gemini.genai.configure"),
            patch("apps.ai.gemini.genai.list_models", return_value=_fake_model_list()),
        ):
            return GeminiProvider(api_key="dummy-key-for-test")

    def test_system_message_goes_to_system_instruction_not_contents(self):
        provider = self._make_provider()
        mock_response = MagicMock(text="ヒント: まず公式を思い出してみましょう")

        with patch("apps.ai.gemini.genai.GenerativeModel") as MockModel:
            MockModel.return_value.generate_content.return_value = mock_response

            result = provider.chat(
                [
                    ChatMessage(role="system", content="You are an AI Tutor."),
                    ChatMessage(role="user", content="三平方の定理を教えて"),
                ]
            )

            self.assertEqual(result.text, "ヒント: まず公式を思い出してみましょう")
            # JA: system_instructionに渡ったか / VI: Có truyền vào system_instruction chưa
            _, kwargs = MockModel.call_args
            self.assertEqual(kwargs["system_instruction"], "You are an AI Tutor.")
            # JA: contentsにsystemメッセージが混ざっていないか
            # VI: contents không lẫn tin nhắn system
            contents = MockModel.return_value.generate_content.call_args[0][0]
            self.assertEqual(contents, [{"role": "user", "parts": ["三平方の定理を教えて"]}])

    def test_conversation_history_is_sent_with_correct_roles(self):
        # JA: これが以前のバグの核心: 履歴(assistant含む)が全部Geminiに届くこと。
        # VI: Đây là cốt lõi bug trước đây: toàn bộ lịch sử (kể cả assistant) phải tới Gemini.
        provider = self._make_provider()
        mock_response = MagicMock(text="続きのヒント")

        with patch("apps.ai.gemini.genai.GenerativeModel") as MockModel:
            MockModel.return_value.generate_content.return_value = mock_response

            provider.chat(
                [
                    ChatMessage(role="system", content="You are an AI Tutor."),
                    ChatMessage(role="user", content="質問1"),
                    ChatMessage(role="assistant", content="回答1"),
                    ChatMessage(role="user", content="質問2"),
                ]
            )

            contents = MockModel.return_value.generate_content.call_args[0][0]
            self.assertEqual(
                contents,
                [
                    {"role": "user", "parts": ["質問1"]},
                    {"role": "model", "parts": ["回答1"]},
                    {"role": "user", "parts": ["質問2"]},
                ],
            )

    def test_dict_messages_are_also_supported(self):
        # JA: services.py は AIChatMessage を使うが、契約上 dict も受け付けられるべき
        #     (fake.py と同じ防御的な読み方)。
        # VI: services.py dùng AIChatMessage, nhưng theo hợp đồng vẫn phải nhận được dict
        #     (đọc phòng thủ giống fake.py).
        provider = self._make_provider()
        mock_response = MagicMock(text="ok")

        with patch("apps.ai.gemini.genai.GenerativeModel") as MockModel:
            MockModel.return_value.generate_content.return_value = mock_response

            provider.chat([{"role": "user", "content": "dictでも動く？"}])

            contents = MockModel.return_value.generate_content.call_args[0][0]
            self.assertEqual(contents, [{"role": "user", "parts": ["dictでも動く？"]}])

    def test_empty_messages_sends_single_empty_user_turn(self):
        provider = self._make_provider()
        mock_response = MagicMock(text="ok")

        with patch("apps.ai.gemini.genai.GenerativeModel") as MockModel:
            MockModel.return_value.generate_content.return_value = mock_response

            provider.chat([])

            contents = MockModel.return_value.generate_content.call_args[0][0]
            self.assertEqual(contents, [{"role": "user", "parts": [""]}])

    def test_retries_on_rate_limit_then_succeeds(self):
        provider = self._make_provider()
        mock_response = MagicMock(text="ok")
        rate_limit_error = Exception("429 Too Many Requests")

        with (
            patch("apps.ai.gemini.genai.GenerativeModel") as MockModel,
            patch("apps.ai.gemini.time.sleep") as mock_sleep,
        ):
            MockModel.return_value.generate_content.side_effect = [
                rate_limit_error,
                mock_response,
            ]

            result = provider.chat([ChatMessage(role="user", content="hi")])

            self.assertEqual(result.text, "ok")
            self.assertEqual(MockModel.return_value.generate_content.call_count, 2)
            mock_sleep.assert_called_once()

    def test_non_rate_limit_error_fails_immediately_without_retry(self):
        provider = self._make_provider()

        with patch("apps.ai.gemini.genai.GenerativeModel") as MockModel:
            MockModel.return_value.generate_content.side_effect = Exception("invalid api key")

            result = provider.chat([ChatMessage(role="user", content="hi")])

            self.assertEqual(MockModel.return_value.generate_content.call_count, 1)
            self.assertIn("[AI Tutor Error]", result.text)


class FakeProviderTests(SimpleTestCase):
    def test_echoes_last_user_message(self):
        result = FakeProvider().chat(
            [
                ChatMessage(role="system", content="ignored"),
                ChatMessage(role="user", content="こんにちは"),
                ChatMessage(role="assistant", content="ignored too"),
            ]
        )
        self.assertEqual(result.text, "[fake-ai] echo: こんにちは")
