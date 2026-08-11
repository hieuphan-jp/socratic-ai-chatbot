"""
apps/ai/client.py

JA: プロバイダ選択の単一窓口。アプリの他所は必ず get_llm() 経由で LLM を得る。
    どの実装を使うかは settings.AI_PROVIDER（＝環境変数）で決まる。呼び出し側は
    fake か gemini かを一切知らずに済む＝ここが唯一の分岐点。
    使い方: `from apps.ai.client import get_llm` → `get_llm().chat([...])`
VI: Cửa duy nhất để chọn provider. Mọi nơi khác trong app phải lấy LLM qua get_llm().
    Dùng hiện thực nào do settings.AI_PROVIDER (biến môi trường) quyết định. Bên gọi
    hoàn toàn không cần biết là fake hay gemini = đây là điểm rẽ nhánh duy nhất.
    Cách dùng: `from apps.ai.client import get_llm` → `get_llm().chat([...])`
"""

from django.conf import settings

from .base import LLMProvider
from .fake import FakeProvider
from .gemini import GeminiProvider


def get_llm() -> LLMProvider:
    provider = getattr(settings, "AI_PROVIDER", "fake")

    if provider == "gemini":
        api_key = getattr(settings, "GEMINI_API_KEY", "")
        # JA: キー未設定なら安全側に倒して fake を返す（開発を止めない）。
        # VI: Chưa có key thì thiên về an toàn, trả về fake (không chặn phát triển).
        if not api_key:
            return FakeProvider()
        return GeminiProvider(api_key=api_key)

    # JA: 既定は fake。VI: Mặc định là fake.
    return FakeProvider()
