"""
config/settings/production.py

JA: 本番用の設定のスケルトン。DB は環境変数から PostgreSQL を組み立てられる形にし、
    秘密情報は必ず環境変数で注入する。今はまだデプロイしないので最小限。
    「SQLite から PostgreSQL へ後で切替できる」という要件の受け皿がここ。
VI: Bộ khung cấu hình production. DB dựng PostgreSQL từ biến môi trường, secret luôn
    tiêm qua biến môi trường. Hiện chưa deploy nên giữ tối thiểu. Đây là nơi hiện thực
    yêu cầu "sau này chuyển từ SQLite sang PostgreSQL".
"""

import os

from .base import *  # noqa: F401,F403

DEBUG = False

# JA: 本番ホストは環境変数から。カンマ区切りで複数指定可。
# VI: Host production lấy từ biến môi trường, phân tách bằng dấu phẩy.
ALLOWED_HOSTS = [h for h in os.environ.get("DJANGO_ALLOWED_HOSTS", "").split(",") if h]

# JA: PostgreSQL への切替口。環境変数が揃っていれば PostgreSQL を使う。
# VI: Điểm chuyển sang PostgreSQL. Nếu đủ biến môi trường thì dùng PostgreSQL.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", ""),
        "USER": os.environ.get("POSTGRES_USER", ""),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", ""),
        "HOST": os.environ.get("POSTGRES_HOST", "localhost"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
    }
}

# JA: 本番は Cookie を HTTPS 限定にするなどの強化をここで行う（担当が後で拡張）。
# VI: Ở production tăng cường bảo mật Cookie chỉ qua HTTPS... (người phụ trách mở rộng sau).
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

AI_PROVIDER = os.environ.get("AI_PROVIDER", "gemini")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# JA: 分岐推定の方式(ai / bigram / off)。詳細は local.py のコメントを参照。
# VI: Phương thức đoán nhánh (ai / bigram / off). Xem chú thích ở local.py.
CHAT_BRANCHING_STRATEGY = os.environ.get("CHAT_BRANCHING_STRATEGY", "ai")
