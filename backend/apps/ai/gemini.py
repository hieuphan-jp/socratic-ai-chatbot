"""
apps/ai/gemini.py

JA: Gemini Flash 実装の「スケルトン」。中身は未実装で、AI 担当が後で埋める。
    ここで重要なのは、fake と全く同じ契約(base.LLMProvider)を満たすこと。
    そうすれば client.py が環境変数で fake ⇄ gemini を無変更で切り替えられる。
    ★キーが無い環境では client がこの実装を選ばないので、未実装でも全体は壊れない。
VI: "Bộ khung" cho hiện thực Gemini Flash. Phần thân chưa cài, người phụ trách AI điền sau.
    Điều quan trọng: thỏa đúng hợp đồng (base.LLMProvider) y như fake.
    Nhờ đó client.py chuyển fake ⇄ gemini qua biến môi trường mà không sửa code.
    ★Ở môi trường không có key, client sẽ không chọn hiện thực này nên chưa cài vẫn không hỏng.
"""

from .base import ChatMessage, ChatResult


class GeminiProvider:
    def __init__(self, api_key: str):
        # JA: キーを保持するだけ。実際の SDK 初期化は担当が実装する。
        # VI: Chỉ lưu key. Khởi tạo SDK thật do người phụ trách cài.
        self._api_key = api_key

    def chat(self, messages: list[ChatMessage]) -> ChatResult:
        # JA: TODO(ai担当): Gemini Flash API を呼び、応答テキストを ChatResult に詰める。
        #     httpx 等で REST を叩く / SDK を使う、のいずれかを選ぶ。fake と同じ形で返すこと。
        # VI: TODO(người phụ trách ai): Gọi Gemini Flash API, đóng gói text vào ChatResult.
        #     Chọn gọi REST bằng httpx... hoặc dùng SDK. Trả về cùng hình dạng như fake.
        raise NotImplementedError(
            "GeminiProvider は未実装です。AI 担当が実装してください / "
            "GeminiProvider chưa được cài. Người phụ trách AI hãy hiện thực."
        )
