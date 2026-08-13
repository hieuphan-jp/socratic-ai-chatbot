"""
apps/ai/fake.py

JA: API キー不要で動く決定的な fake 実装。これが「全員がキー無しで開発できる」の核心。
    外部通信を一切せず、入力から機械的に応答を作る（決定的なのでテストにも使える）。
    ★この実装は base.LLMProvider の契約を満たす。呼び出し側は fake か gemini かを意識しない。

    ★履歴: 一時 base.py から ChatMessage/ChatResult を削除した際、ここも str を直接
      返すよう変更したが、実際の services.py は ChatMessage/ChatResult に依存していた
      ため ImportError になった。ChatResult を返す形に戻し、gemini.py 側も
      ChatResult を返すよう揃えることで契約を統一した。
      あわせて messages の各要素は role/content 属性を持つオブジェクト
      (AIChatMessage) と dict の両方を受け付けられるよう防御的に実装している。
VI: Hiện thực fake chạy được mà không cần API key. Đây là cốt lõi của "mọi người dev không cần key".
    Không gọi mạng ngoài, tạo phản hồi cơ học từ đầu vào (tất định nên dùng cho test được).
    ★Hiện thực này thỏa hợp đồng base.LLMProvider. Bên gọi không phân biệt fake hay gemini.

    ★Lịch sử: Trước đó khi xóa ChatMessage/ChatResult khỏi base.py, file này cũng bị
      đổi để trả thẳng str, nhưng services.py thực tế lại phụ thuộc vào
      ChatMessage/ChatResult nên gây ImportError. Nay trả lại ChatResult, đồng thời
      gemini.py cũng được chỉnh để trả ChatResult, thống nhất hợp đồng cho cả hai.
      Phần đọc messages vẫn giữ cách viết phòng thủ, nhận cả object có thuộc tính
      role/content (AIChatMessage) lẫn dict {"role":..., "content":...}.
"""

from .base import ChatMessage, ChatResult


class FakeProvider:
    def chat(self, messages: list[ChatMessage]) -> ChatResult:
        # JA: 最後のユーザー発話をそのまま反射して返すだけの単純実装。
        # VI: Hiện thực đơn giản: phản chiếu lại phát ngôn người dùng cuối cùng.
        last_user = ""
        for m in reversed(messages):
            role = getattr(m, "role", None)
            content = getattr(m, "content", None)

            if role is None and isinstance(m, dict):
                role = m.get("role")
            if content is None and isinstance(m, dict):
                content = m.get("content")

            if role == "user":
                last_user = content or ""
                break

        return ChatResult(text=f"[fake-ai] echo: {last_user}")