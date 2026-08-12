import google.generativeai as genai
from .base import LLMProvider


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
                m.name for m in genai.list_models()
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

    def chat(self, messages) -> str:
        try:
            if isinstance(messages, list) and len(messages) > 0:
                last_msg = messages[-1]
                if hasattr(last_msg, "content"):
                    prompt = last_msg.content
                elif isinstance(last_msg, dict):
                    prompt = last_msg.get("content", str(last_msg))
                else:
                    prompt = str(last_msg)
            else:
                prompt = str(messages)

            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"[AI Tutor Error] Lỗi khi gọi Gemini API: {str(e)}"