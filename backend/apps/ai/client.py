import os
from functools import lru_cache

from django.conf import settings

from .base import LLMProvider
from .fake import FakeProvider

# JA: GeminiProvider は google-generativeai パッケージに依存するため、
#     ここでは import しない。トップレベルで import すると、パッケージが
#     インストールされていない環境では client.py を import した時点で
#     ModuleNotFoundError が発生し、AI_PROVIDER=fake の場合でも落ちてしまう。
#     → get_llm() の中で「本当に gemini を使うときだけ」遅延 import する。
# VI: GeminiProvider phụ thuộc vào package google-generativeai, nên KHÔNG
#     import ở đây (top-level). Nếu import ở đầu file, máy nào chưa cài
#     package sẽ bị ModuleNotFoundError ngay khi import client.py — kể cả
#     khi AI_PROVIDER=fake và không hề dùng tới Gemini.
#     → Chỉ import GeminiProvider bên trong get_llm(), khi thực sự cần dùng
#        (lazy import), để cô lập lỗi thiếu package vào đúng nhánh gemini.

# JA: ★ここでは load_dotenv() を呼ばない。config/settings/base.py が
#     Django起動時に必ず1回だけリポジトリ直下の .env を読み込んでおり、
#     manage.py の実行時点でos.environに反映済みだからである。
#     以前はここでも backend/.env を override=True で読み直しており、
#     「ルートの.envとbackend/.envの内容が食い違うと、後から読んだ方が
#     常に勝つ」という分かりにくい二重管理になっていた
#     (実際にAI_PROVIDER設定が食い違って気づきにくい形で反映されない事故が発生した)。
#     読み込み元をbase.pyの1箇所に一本化し、事故の芽を断つ。
# VI: ★Không gọi load_dotenv() ở đây nữa. config/settings/base.py đã nạp
#     đúng 1 lần file .env ở gốc repo khi Django khởi động, và giá trị đã
#     có trong os.environ ngay khi manage.py bắt đầu chạy.
#     Trước đây ở đây còn đọc lại backend/.env với override=True, tạo ra
#     kiểu quản lý kép khó hiểu: "nếu nội dung .env gốc và backend/.env
#     lệch nhau thì file đọc SAU luôn thắng" (thực tế đã xảy ra sự cố
#     AI_PROVIDER bị lệch mà rất khó nhận ra). Gom về một nguồn duy nhất
#     (base.py) để loại bỏ nguy cơ này.


@lru_cache(maxsize=1)
def get_llm() -> LLMProvider:
    """
    JA: ★重要: @lru_cache でプロセス内シングルトン化。
        以前は毎リクエストごとに GeminiProvider を new していたため、
        コンストラクタ内の _get_working_model() が呼ぶ genai.list_models() も
        毎回実行され、実際の応答生成 (generate_content) と合わせて
        「1メッセージ = 2回の Gemini API 呼び出し」になっていた。
        これが 2 通目のメッセージ程度で 429 (Too Many Requests) が出ていた主因。
        シングルトン化により list_models() はプロセス起動後 1 回だけになる。
    VI: ★Quan trọng: dùng @lru_cache để biến hàm này thành singleton trong
        suốt vòng đời process. Trước đây mỗi request đều tạo GeminiProvider
        MỚI, khiến genai.list_models() bên trong _get_working_model() cũng
        bị gọi lại mỗi lần — cộng với generate_content() thực tế là
        "1 tin nhắn = 2 lần gọi API Gemini". Đây là nguyên nhân chính khiến
        mới hỏi câu thứ 2 đã dính lỗi 429 (Too Many Requests). Sau khi
        singleton hóa, list_models() chỉ chạy đúng 1 lần khi process khởi động.
    """
    provider = os.getenv("AI_PROVIDER", "fake").strip()
    api_key = os.getenv("GEMINI_API_KEY", "").strip() or getattr(settings, "GEMINI_API_KEY", "")

    if provider == "gemini" and api_key:
        try:
            # JA: 遅延 import。ここで初めて google.generativeai を読み込む。
            # VI: Import trễ. Chỉ tới đây mới thực sự nạp google.generativeai.
            from .gemini import GeminiProvider

            return GeminiProvider(api_key=api_key)
        except (ImportError, ModuleNotFoundError) as e:
            # JA: パッケージが未インストールの環境 → fake にフォールバック
            # VI: Máy chưa cài package google-generativeai → rơi về fake
            print(
                f"[AI Provider] Thiếu package 'google-generativeai', dùng FakeProvider thay thế. Chi tiết: {e}"
            )
        except Exception as e:
            # JA: API キー不正・ネットワークエラーなど、その他の初期化失敗 → fake にフォールバック
            # VI: Lỗi khác khi khởi tạo Gemini (API key sai, lỗi mạng, model không khả dụng, v.v.)
            #     → rơi về fake
            print(
                f"[AI Provider] Không thể khởi tạo GeminiProvider, dùng FakeProvider thay thế. Chi tiết: {e}"
            )

    return FakeProvider()
