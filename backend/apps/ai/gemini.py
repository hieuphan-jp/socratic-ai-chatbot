import logging

import google.generativeai as genai

from .base import ChatResult, LLMProvider

logger = logging.getLogger(__name__)


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

        # JA: ★リトライはしない(1回だけ試す)。
        #     以前は429時に3秒→6秒待って最大2回リトライしていたが、Google側が
        #     実際に指示してくる待機時間(数十秒)より遥かに短く、リトライは
        #     ほぼ必ず失敗していた。しかも失敗したリトライもクォータを消費するため、
        #     「1回の送信で最大3回分のクォータを溶かすのに、成功率はほぼ0」という
        #     逆効果な実装になっていた。ここでは1回だけ試し、失敗したら理由が
        #     分かるメッセージをそのまま返す。再試行するかはユーザーの判断に委ねる
        #     (送信ボタンを再度押すだけで良い)。
        # VI: ★Không retry (chỉ thử 1 lần).
        #     Trước đây khi gặp 429 sẽ đợi 3s→6s rồi retry tối đa 2 lần, nhưng thời
        #     gian đó ngắn hơn nhiều so với thời gian Google thực sự yêu cầu đợi (vài
        #     chục giây), nên retry gần như luôn thất bại. Hơn nữa các lần retry thất
        #     bại vẫn tốn quota, nên thành ra "1 lần gửi tốn tối đa 3 lần quota mà tỉ lệ
        #     thành công gần như 0" — phản tác dụng. Ở đây chỉ thử 1 lần, thất bại thì
        #     trả thẳng thông báo lý do. Có retry lại hay không là quyết định của user
        #     (chỉ cần bấm gửi lại).
        try:
            response = model.generate_content(contents)
            return ChatResult(text=response.text)
        except Exception as e:
            # JA: ★デバッグ用: Google 側の生エラーをそのままログ出力する。
            #     quota_metric / quota_id が含まれていれば、RPM (分単位) なのか
            #     RPD (日単位) なのか、正確な原因が分かる。
            # VI: ★Debug: log nguyên văn lỗi gốc từ Google. Nếu có chứa
            #     quota_metric / quota_id thì sẽ biết chính xác là quota theo
            #     PHÚT (RPM) hay theo NGÀY (RPD) đang bị chạm.
            logger.error("[Gemini] リクエスト失敗。種別: %s | 詳細: %r", type(e).__name__, e)

            if _is_rate_limit_error(e):
                return ChatResult(
                    text=(
                        "[AI Tutor] Geminiの利用回数制限(429)に達しました。しばらく待ってから、"
                        "もう一度送信してください。 / "
                        "Đã đạt giới hạn số lượt gọi Gemini (429). Vui lòng đợi một chút rồi gửi lại."
                    )
                )
            return ChatResult(
                text=(
                    f"[AI Tutor] Geminiの呼び出しでエラーが発生しました: {e} / "
                    f"Đã xảy ra lỗi khi gọi Gemini: {e}"
                )
            )
