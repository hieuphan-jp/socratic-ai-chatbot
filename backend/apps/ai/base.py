"""
apps/ai/base.py

JA: LLM プロバイダの共通インターフェイス（契約）を Protocol で定義する。
    実装（fake / gemini）はこの契約を満たすだけでよく、呼び出し側は具体実装を知らない。
    こうして「APIキーが無くても fake で開発でき、後から gemini に差し替えられる」を実現する。
    ★継承ではなく Protocol にするのは、実装クラスに import 依存を強制しない（疎結合）ため。
VI: Định nghĩa giao diện chung (hợp đồng) của nhà cung cấp LLM bằng Protocol.
    Các hiện thực (fake / gemini) chỉ cần thỏa hợp đồng; bên gọi không biết hiện thực cụ thể.
    Nhờ đó: "không cần API key vẫn phát triển được bằng fake, sau này thay bằng gemini".
    ★Dùng Protocol thay vì kế thừa để không ép hiện thực phụ thuộc import (lỏng lẻo).
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
    JA: 全プロバイダが満たすべき契約。まずは chat() だけを定義する。
        引数・戻り値の型を固定することで、呼び出し側は実装を差し替えても壊れない。
    VI: Hợp đồng mọi provider phải thỏa. Trước mắt chỉ định nghĩa chat().
        Cố định kiểu tham số/trả về để bên gọi không hỏng khi thay hiện thực.
    """

    def chat(self, messages: list[ChatMessage]) -> ChatResult:
        """JA: 会話履歴を受け取り応答を返す。VI: Nhận lịch sử hội thoại và trả lời."""
        ...
