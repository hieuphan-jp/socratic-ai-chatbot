"""
apps/ai/base.py

JA: LLM プロバイダの共通インターフェイス（契約）を Protocol で定義する。
    実装（fake / gemini）はこの契約を満たすだけでよく、呼び出し側は具体実装を知らない。
    こうして「APIキーが無くても fake で開発でき、後から gemini に差し替えられる」を実現する。
    ★継承ではなく Protocol にするのは、実装クラスに import 依存を強制しない（疎結合）ため。

    ★履歴: 一時 ChatMessage/ChatResult を「未使用」と判断して削除したが、
      services.py が実際に `AIChatMessage` / `ChatResult` を import して使っていたため
      ImportError が発生した。ここで復元し、gemini.py / fake.py の chat() が
      両方とも ChatResult を返すよう揃えることで、契約と実装のズレを解消した。
VI: Định nghĩa giao diện chung (hợp đồng) của nhà cung cấp LLM bằng Protocol.
    Các hiện thực (fake / gemini) chỉ cần thỏa hợp đồng; bên gọi không biết hiện thực cụ thể.
    Nhờ đó: "không cần API key vẫn phát triển được bằng fake, sau này thay bằng gemini".
    ★Dùng Protocol thay vì kế thừa để không ép hiện thực phụ thuộc import (lỏng lẻo).

    ★Lịch sử: Trước đó đã xóa nhầm ChatMessage/ChatResult vì tưởng không ai dùng, nhưng
      thực tế services.py có import `AIChatMessage` / `ChatResult` từ đây → gây ImportError.
      Nay khôi phục lại, đồng thời chỉnh gemini.py / fake.py để cả hai đều trả về
      ChatResult, giúp hợp đồng (Protocol) và hiện thực thực sự khớp nhau.
"""

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class ChatMessage:
    """JA: 1つの会話メッセージ。VI: Một tin nhắn hội thoại. role: "user" | "assistant" | "system"."""

    role: str
    content: str


@dataclass(frozen=True)
class ChatResult:
    """JA: 生成結果。text 以外の項目は担当が後で足してよい。VI: Kết quả sinh; có thể thêm trường sau."""

    text: str


@runtime_checkable
class LLMProvider(Protocol):
    """
    JA: 全プロバイダが満たすべき契約。chat() は ChatMessage のリストを受け取り、
        必ず ChatResult を返すこと（gemini.py / fake.py の両方が遵守する）。
    VI: Hợp đồng mọi provider phải thỏa. chat() nhận list ChatMessage,
        và LUÔN trả về ChatResult (cả gemini.py lẫn fake.py đều phải tuân theo).
    """

    def chat(self, messages: list[ChatMessage]) -> ChatResult:
        """JA: 会話履歴を受け取り応答を返す。VI: Nhận lịch sử hội thoại và trả lời."""
        ...
