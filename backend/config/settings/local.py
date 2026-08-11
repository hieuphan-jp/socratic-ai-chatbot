"""
config/settings/local.py

JA: ローカル開発用の設定。base を継承し、SQLite・DEBUG・緩い CORS を有効化する。
    manage.py はこのファイルを既定で読む。秘密情報はここに書かない。
VI: Cấu hình phát triển cục bộ. Kế thừa base, bật SQLite, DEBUG và CORS lỏng.
    manage.py mặc định đọc file này. Không ghi secret ở đây.
"""

import os

from .base import *  # noqa: F401,F403
from .base import BASE_DIR

DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

# JA: SQLite を使う。後で PostgreSQL に切替できるよう DATABASE_URL 風の分岐は
#     production 側に置き、local は常に SQLite で固定（誰でもすぐ起動できる）。
# VI: Dùng SQLite. Việc chuyển sang PostgreSQL để ở production; local luôn cố định
#     SQLite để ai cũng chạy được ngay.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# JA: Vite 開発サーバ(5173) からの Cookie 付きリクエストを許可する。
#     セッション認証のため credentials を許可し、Origin はホワイトリスト方式。
# VI: Cho phép request kèm Cookie từ Vite dev server (5173). Vì dùng session auth
#     nên bật credentials, Origin theo danh sách trắng.
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
CORS_ALLOW_CREDENTIALS = True

# JA: フロントは別オリジン(5173)なので CSRF の信頼 Origin に追加する。
# VI: Frontend khác origin (5173) nên thêm vào danh sách tin cậy CSRF.
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

# JA: AI プロバイダの切替。既定は fake（APIキー不要で全員が動かせる）。
# VI: Chọn nhà cung cấp AI. Mặc định fake (không cần API key, ai cũng chạy được).
AI_PROVIDER = os.environ.get("AI_PROVIDER", "fake")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
