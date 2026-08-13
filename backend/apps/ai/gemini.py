import logging
import time

import google.generativeai as genai

from .base import ChatResult, LLMProvider

logger = logging.getLogger(__name__)

MAX_RETRIES = 2
BACKOFF_SECONDS = [
    3,
    6,
]  # JA: 1回目失敗後3秒待機、2回目失敗後6秒待機 / VI: Thất bại lần 1 đợi 3s, lần 2 đợi 6s


def _is_rate_limit_error(e: Exception) -> bool:
    error_str = str(e)
    return (
        "429" in error_str
        or "ResourceExhausted" in type(e).__name__
        or "quota" in error_str.lower()
    )


class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        genai.configure(api_key=self.api_key)
        self.model = self._get_working_model()

    def _get_working_model(self):
        preferred_models = [
            "models/gemini-3.5-flash",
            "models/gemini-flash-latest",
            "models/gemini-3.1-flash-lite",
            "models/gemini-pro-latest",
        ]

        try:
            available_models = [
                m.name
                for m in genai.list_models()
                if "generateContent" in m.supported_generation_methods
            ]

            for pref in preferred_models:
                if pref in available_models:
                    return genai.GenerativeModel(pref)

            for m in available_models:
                if "gemini-2.5" not in m and ("flash" in m or "pro" in m):
                    return genai.GenerativeModel(m)
        except Exception:
            pass

        return genai.GenerativeModel("models/gemini-3.5-flash")

    def _messages_to_prompt(self, messages) -> str:
        """
        JA: ★重要な修正: 以前は messages[-1] (最後の1件) しか使っていなかったため、
            system プロンプト（家庭教師としての指示）と過去の会話履歴が
            Gemini に一切送られていなかった（＝毎回「記憶喪失」状態だった）。
            ここでリスト全体を「ROLE: content」形式のテキストに結合し、
            system指示・会話履歴・新しい質問がすべて Gemini に渡るようにする。
        VI: ★Sửa lỗi quan trọng: Trước đây chỉ dùng messages[-1] (tin nhắn cuối),
            khiến system prompt (chỉ thị đóng vai gia sư) và lịch sử hội thoại
            KHÔNG BAO GIỜ được gửi tới Gemini (=mỗi lần hỏi Gemini đều "mất trí nhớ").
            Ở đây ghép TOÀN BỘ danh sách thành text dạng "ROLE: nội dung",
            để cả system, lịch sử hội thoại, và câu hỏi mới đều được gửi đủ.
        """
        if not isinstance(messages, list) or len(messages) == 0:
            return str(messages)

        lines = []
        for m in messages:
            if hasattr(m, "role") and hasattr(m, "content"):
                role, content = m.role, m.content
            elif isinstance(m, dict):
                role, content = m.get("role", "user"), m.get("content", str(m))
            else:
                role, content = "user", str(m)
            lines.append(f"{role.upper()}: {content}")

        return "\n\n".join(lines)

    def chat(self, messages) -> ChatResult:
        prompt = self._messages_to_prompt(messages)
        last_error: Exception | None = None

        for attempt in range(MAX_RETRIES + 1):
            try:
                response = self.model.generate_content(prompt)
                return ChatResult(text=response.text)
            except Exception as e:
                last_error = e
                logger.error(
                    "[Gemini] Lần thử %s/%s thất bại. Loại lỗi: %s | Chi tiết: %r",
                    attempt + 1,
                    MAX_RETRIES + 1,
                    type(e).__name__,
                    e,
                )
                if _is_rate_limit_error(e) and attempt < MAX_RETRIES:
                    time.sleep(BACKOFF_SECONDS[attempt])
                    continue
                break

        error_str = str(last_error)
        if _is_rate_limit_error(last_error):
            return ChatResult(
                text=(
                    "[AI Tutor] Hệ thống Gemini đang bị giới hạn số lượt gọi trong phút này "
                    "(429 - Too Many Requests / hết quota), đã thử lại nhưng vẫn chưa được. "
                    "Vui lòng đợi khoảng 30-60 giây rồi thử lại."
                )
            )
        return ChatResult(text=f"[AI Tutor Error] Lỗi khi gọi Gemini API: {error_str}")
