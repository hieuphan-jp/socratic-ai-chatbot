import os
from pathlib import Path
from django.conf import settings
from dotenv import load_dotenv

from .base import LLMProvider
from .fake import FakeProvider
from .gemini import GeminiProvider

# Load biến môi trường từ file .env tại thư mục gốc backend
BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env", override=True)


def get_llm() -> LLMProvider:
    provider = os.getenv("AI_PROVIDER", "fake").strip()
    api_key = os.getenv("GEMINI_API_KEY", "").strip() or getattr(settings, "GEMINI_API_KEY", "")

    if provider == "gemini" and api_key:
        try:
            return GeminiProvider(api_key=api_key)
        except Exception:
            pass

    return FakeProvider()