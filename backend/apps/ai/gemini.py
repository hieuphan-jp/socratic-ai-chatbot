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


def _to_role_and_content(message) -> tuple[str, str]:
    """
    JA: AIChatMessage(role/content属性を持つオブジェクト)と、dict {"role":..,"content":..}
        の両方を受け付ける(fake.pyの防御的な読み方に合わせる)。
    VI: Nhận cả AIChatMessage (object có thuộc tính role/content) lẫn dict
        {"role":.., "content":..} (giống cách đọc phòng thủ của fake.py).
    """
    role = getattr(message, "role", None)
    content = getattr(message, "content", None)
    if role is None and isinstance(message, dict):
        role = message.get("role")
    if content is None and isinstance(message, dict):
        content = message.get("content")
    return role or "user", content or ""


class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        genai.configure(api_key=self.api_key)
        # JA: ★モデル名(文字列)だけをここで解決してキャッシュする。GeminiProviderは
        #     get_llm()経由でプロセス内シングルトンなので、genai.list_models()は
        #     プロセス起動後1回だけ実行される。GenerativeModel自体はネットワーク
        #     通信を伴わない軽量なラッパーなので、chat()の中でリクエストごとに
        #     system_instructionを変えて作り直してよい。
        # VI: ★Chỉ giải quyết và cache TÊN model (chuỗi) ở đây. Vì GeminiProvider là
        #     singleton trong process (qua get_llm()), genai.list_models() chỉ chạy
        #     đúng 1 lần khi process khởi động. Bản thân GenerativeModel là wrapper
        #     nhẹ, không gọi mạng, nên có thể tạo lại mỗi request trong chat() với
        #     system_instruction khác nhau.
        self.model_name = self._resolve_model_name()

    def _resolve_model_name(self) -> str:
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
                    return pref

            for m in available_models:
                if "gemini-2.5" not in m and ("flash" in m or "pro" in m):
                    return m
        except Exception:
            pass

        return "models/gemini-3.5-flash"

    def chat(self, messages) -> ChatResult:
        # JA: ★system役割のメッセージはsystem_instructionへ、それ以外(user/assistant)は
        #     Geminiの複数ターン形式(role: user/model)に変換する。以前はmessages[-1]
        #     しか送っておらず、システムプロンプトと会話履歴が丸ごと無視されていた。
        # VI: ★Tin nhắn role "system" đưa vào system_instruction, còn lại (user/assistant)
        #     chuyển sang định dạng nhiều lượt của Gemini (role: user/model). Trước đây
        #     chỉ gửi messages[-1], bỏ qua toàn bộ system prompt và lịch sử hội thoại.
        system_instruction = None
        contents = []
        for message in messages if isinstance(messages, list) else [messages]:
            role, content = _to_role_and_content(message)
            if role == "system":
                # JA: systemは1メッセージ想定。複数あれば連結する。
                # VI: Giả định chỉ có 1 tin system; nếu có nhiều thì nối lại.
                system_instruction = (
                    f"{system_instruction}\n\n{content}" if system_instruction else content
                )
                continue
            gemini_role = "model" if role == "assistant" else "user"
            contents.append({"role": gemini_role, "parts": [content]})

        if not contents:
            contents = [{"role": "user", "parts": [""]}]

        model = genai.GenerativeModel(self.model_name, system_instruction=system_instruction)

        last_error: Exception | None = None

        # JA: 429 の場合のみ、指数バックオフしながら最大 MAX_RETRIES 回リトライする。
        #     それ以外のエラー（不正な入力、ネットワーク断など）は即座に失敗として返す。
        # VI: CHỈ retry khi gặp lỗi 429, đợi tăng dần (backoff) tối đa MAX_RETRIES lần.
        #     Các lỗi khác (input sai, mất mạng, v.v.) trả lỗi ngay, không retry.
        for attempt in range(MAX_RETRIES + 1):
            try:
                response = model.generate_content(contents)
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
