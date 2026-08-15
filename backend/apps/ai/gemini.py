import logging
import time

import google.generativeai as genai

from .base import ChatResult, LLMProvider

logger = logging.getLogger(__name__)

# JA: 429 (レート制限) 時のリトライ設定。
# VI: Cấu hình retry khi gặp lỗi 429 (rate limit).
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
        # JA: これはコンストラクタから1回だけ呼ばれる (get_llm() が @lru_cache で
        #     シングルトン化されたため)。genai.list_models() はここでのみ実行される。
        # VI: Hàm này chỉ được gọi 1 lần từ constructor (vì get_llm() đã singleton
        #     hóa bằng @lru_cache). genai.list_models() chỉ chạy đúng ở đây, 1 lần.
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

    def chat(self, messages) -> ChatResult:
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

        last_error: Exception | None = None

        # JA: 429 の場合のみ、指数バックオフしながら最大 MAX_RETRIES 回リトライする。
        #     それ以外のエラー（不正な入力、ネットワーク断など）は即座に失敗として返す。
        # VI: CHỈ retry khi gặp lỗi 429, đợi tăng dần (backoff) tối đa MAX_RETRIES lần.
        #     Các lỗi khác (input sai, mất mạng, v.v.) trả lỗi ngay, không retry.
        for attempt in range(MAX_RETRIES + 1):
            try:
                response = self.model.generate_content(prompt)
                return ChatResult(text=response.text)
            except Exception as e:
                last_error = e
                # JA: ★デバッグ用: Google 側の生エラーをそのままログ出力する。
                #     quota_metric / quota_id が含まれていれば、RPM (分単位) なのか
                #     RPD (日単位) なのか、正確な原因が分かる。
                # VI: ★Debug: log nguyên văn lỗi gốc từ Google. Nếu có chứa
                #     quota_metric / quota_id thì sẽ biết chính xác là quota theo
                #     PHÚT (RPM) hay theo NGÀY (RPD) đang bị chạm.
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

        # JA: リトライしても回復しなかった場合の最終エラー処理。
        # VI: Xử lý lỗi cuối cùng nếu retry vẫn không phục hồi được.
        error_str = str(last_error)
        if _is_rate_limit_error(last_error):
            return ChatResult(
                text=(
                    "[AI Tutor] Hệ thống Gemini đang bị giới hạn số lượt gọi trong phút này "
                    "(429 - Too Many Requests / hết quota), đã thử lại nhưng vẫn chưa được. "
                    "Vui lòng đợi khoảng 30-60 giây rồi thử lại. Nếu lỗi này lặp lại thường "
                    "xuyên, cân nhắc kiểm tra hạn mức (quota) tại Google AI Studio hoặc đổi "
                    "sang model có giới hạn request/phút cao hơn."
                )
            )
        return ChatResult(text=f"[AI Tutor Error] Lỗi khi gọi Gemini API: {error_str}")
