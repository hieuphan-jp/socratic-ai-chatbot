"""
apps/ai/fake.py

JA: API キー不要で動く決定的な fake 実装。これが「全員がキー無しで開発できる」の核心。
    外部通信を一切せず、入力から機械的に応答を作る（決定的なのでテストにも使える）。
    ★この実装は base.LLMProvider の契約を満たす。呼び出し側は fake か gemini かを意識しない。
VI: Hiện thực fake chạy được mà không cần API key. Đây là cốt lõi của "mọi người dev không cần key".
    Không gọi mạng ngoài, tạo phản hồi cơ học từ đầu vào (tất định nên dùng cho test được).
    ★Hiện thực này thỏa hợp đồng base.LLMProvider. Bên gọi không phân biệt fake hay gemini.
"""

from .base import ChatMessage, ChatResult


class FakeProvider:
    def chat(self, messages: list[ChatMessage]) -> ChatResult:
        # JA: 最後のユーザー発話をそのまま反射して返すだけの単純実装。
        # VI: Hiện thực đơn giản: phản chiếu lại phát ngôn người dùng cuối cùng.
        last_user = next(
            (m.content for m in reversed(messages) if m.role == "user"),
            "",
        )
        return ChatResult(text=f"[fake-ai] echo: {last_user}")
