"""
apps/ai/claude.py

JA: Anthropic Claude API (有料従量課金) を使う LLMProvider 実装。
    Gemini無料枠のRPM/RPD制限で開発中に頻繁に詰まっていたため追加した。
    Claude APIは無料枠ではなく最初から従量課金なので、「数往復で1日ロックアウト」
    という事態が起きない。base.LLMProvider の契約 (chat() -> ChatResult) は
    gemini.py と同一に保ち、呼び出し側 (services.py) は差異を意識しない。
VI: Hiện thực LLMProvider dùng Anthropic Claude API (trả phí theo lượng dùng).
    Thêm vào vì gói miễn phí của Gemini hay bị chặn RPM/RPD ngay khi đang dev.
    Claude API trả phí theo request ngay từ đầu (không có free-tier quota ngày),
    nên không còn tình trạng "gọi vài lần là bị khóa cả ngày". Hợp đồng
    base.LLMProvider (chat() -> ChatResult) giữ giống hệt gemini.py, phía gọi
    (services.py) không cần biết khác biệt.
"""

import logging
import time

import anthropic

from .base import ChatResult, LLMProvider

logger = logging.getLogger(__name__)

# JA: 429 (レート制限) 時のリトライ設定。gemini.py と揃える。
# VI: Cấu hình retry khi gặp lỗi 429 (rate limit). Giữ giống gemini.py.
MAX_RETRIES = 2
BACKOFF_SECONDS = [3, 6]

# JA: デフォルトモデル。Sonnet系はコスト/品質のバランスが良く、
#     ソクラテス式の対話(質問で気づかせる)にも十分な推論力を持つ。
# VI: Model mặc định. Dòng Sonnet cân bằng tốt giữa chi phí/chất lượng,
#     đủ khả năng suy luận cho kiểu đối thoại Socratic (gợi mở bằng câu hỏi).
DEFAULT_MODEL = "claude-sonnet-5"

# JA: チャットの1返答としては十分な長さ。16000を超えるとSDKがストリーミング必須に
#     なるため、非ストリーミングのまま素早く返せるこの範囲に留める。
# VI: Đủ dài cho 1 câu trả lời chat. Vượt 16000 thì SDK bắt buộc streaming,
#     nên giữ trong khoảng này để trả lời nhanh mà không cần streaming.
MAX_TOKENS = 2048


def _is_billing_error(e: Exception) -> bool:
    """
    JA: プリペイド残高($)を使い切った際のエラーを判定する。自動チャージOFFなら
        課金され続けることはなく、このエラー(403 billing_error)で止まるだけになる。
        anthropic SDKはAPIStatusErrorに`.type`(例: "billing_error")を持つが、
        SDKバージョンで無い場合もあるため、無ければ本文の文言でも判定する。
    VI: Nhận diện lỗi khi hết số dư đã nạp trước ($). Nếu tắt auto-reload thì sẽ
        không bị trừ tiền thêm, request chỉ dừng lại với lỗi này (403 billing_error).
        SDK anthropic có `.type` (vd: "billing_error") trên APIStatusError, nhưng
        vài phiên bản có thể không có, nên nếu thiếu thì kiểm tra theo nội dung lỗi.
    """
    if getattr(e, "type", None) == "billing_error":
        return True
    error_str = str(e).lower()
    return "credit balance" in error_str or "billing_error" in error_str


def _to_role_and_content(message) -> tuple[str, str]:
    """
    JA: AIChatMessage(role/content属性を持つオブジェクト)と、dict {"role":..,"content":..}
        の両方を受け付ける(gemini.pyと同じ防御的な読み方)。
    VI: Nhận cả AIChatMessage (object có thuộc tính role/content) lẫn dict
        {"role":.., "content":..} (giống cách đọc phòng thủ của gemini.py).
    """
    role = getattr(message, "role", None)
    content = getattr(message, "content", None)
    if role is None and isinstance(message, dict):
        role = message.get("role")
    if content is None and isinstance(message, dict):
        content = message.get("content")
    return role or "user", content or ""


class ClaudeProvider(LLMProvider):
    def __init__(self, api_key: str, model: str | None = None):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model or DEFAULT_MODEL

    def chat(self, messages) -> ChatResult:
        # JA: system役割はsystemパラメータへ、それ以外はuser/assistantの
        #     複数ターン形式に変換する(Claude APIはuser/assistantの2ロールのみ)。
        # VI: Tin nhắn role "system" đưa vào tham số system, còn lại chuyển sang
        #     định dạng nhiều lượt user/assistant (Claude API chỉ có 2 role này).
        system_instruction = None
        contents: list[dict] = []
        for message in messages if isinstance(messages, list) else [messages]:
            role, content = _to_role_and_content(message)
            if role == "system":
                system_instruction = (
                    f"{system_instruction}\n\n{content}" if system_instruction else content
                )
                continue
            claude_role = "assistant" if role == "assistant" else "user"
            contents.append({"role": claude_role, "content": content or ""})

        if not contents:
            contents = [{"role": "user", "content": ""}]
        # JA: Claude APIは最初のメッセージがuserである必要がある。
        # VI: Claude API yêu cầu tin nhắn đầu tiên phải là role "user".
        if contents[0]["role"] != "user":
            contents.insert(0, {"role": "user", "content": ""})

        last_error: Exception | None = None

        # JA: レート制限のみ指数バックオフしながら最大 MAX_RETRIES 回リトライする。
        #     それ以外のエラーは即座に失敗として返す。
        # VI: CHỈ retry khi gặp lỗi rate limit, đợi tăng dần tối đa MAX_RETRIES lần.
        #     Các lỗi khác trả lỗi ngay, không retry.
        for attempt in range(MAX_RETRIES + 1):
            try:
                kwargs: dict = {
                    "model": self.model,
                    "max_tokens": MAX_TOKENS,
                    # JA: チャット応答を素早く返すため、思考(thinking)は無効化する。
                    # VI: Tắt thinking để trả lời chat nhanh hơn.
                    "thinking": {"type": "disabled"},
                    "messages": contents,
                }
                if system_instruction:
                    kwargs["system"] = system_instruction
                response = self.client.messages.create(**kwargs)
                text = "".join(
                    block.text for block in response.content if block.type == "text"
                )
                return ChatResult(text=text)
            except anthropic.RateLimitError as e:
                last_error = e
                logger.error(
                    "[Claude] Lần thử %s/%s thất bại (rate limit). Chi tiết: %r",
                    attempt + 1,
                    MAX_RETRIES + 1,
                    e,
                )
                if attempt < MAX_RETRIES:
                    time.sleep(BACKOFF_SECONDS[attempt])
                    continue
                break
            except Exception as e:
                last_error = e
                logger.error(
                    "[Claude] Lần thử %s/%s thất bại. Loại lỗi: %s | Chi tiết: %r",
                    attempt + 1,
                    MAX_RETRIES + 1,
                    type(e).__name__,
                    e,
                )
                # JA: レート制限以外(残高切れ含む)は待ってもリトライしない。
                # VI: Ngoài rate limit ra (kể cả hết số dư) thì không retry.
                break

        # JA: リトライしても回復しなかった場合の最終エラー処理。
        # VI: Xử lý lỗi cuối cùng nếu retry vẫn không phục hồi được.
        error_str = str(last_error)
        if isinstance(last_error, anthropic.RateLimitError):
            return ChatResult(
                text=(
                    "[AI Tutor] Hệ thống Claude đang bị giới hạn số lượt gọi trong phút này "
                    "(429 - Too Many Requests), đã thử lại nhưng vẫn chưa được. "
                    "Vui lòng đợi khoảng 30-60 giây rồi thử lại."
                )
            )
        if last_error is not None and _is_billing_error(last_error):
            return ChatResult(
                text=(
                    "[AI Tutor] Tài khoản Claude API đã dùng hết số dư đã nạp trước "
                    "(hoặc chưa nạp). Vì auto-reload đang tắt nên hệ thống KHÔNG bị tính "
                    "phí thêm, chỉ dừng gọi API tại đây. Vui lòng nạp thêm số dư tại "
                    "Anthropic Console (console.anthropic.com) rồi thử lại."
                )
            )
        return ChatResult(text=f"[AI Tutor Error] Lỗi khi gọi Claude API: {error_str}")
