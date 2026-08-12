"""
config/settings/base.py

JA: 全環境で共通する設定。ここには「環境に依存しない」ものだけを書く。
    DB のホストや DEBUG など環境ごとに変わる値は local / production 側で上書きする。
    設定を分割するのは、ローカルの SQLite と本番の PostgreSQL を無理なく共存させ、
    秘密情報を production 側に隔離するため。
VI: Cấu hình dùng chung cho mọi môi trường. Chỉ đặt ở đây những giá trị KHÔNG phụ
    thuộc môi trường. Giá trị thay đổi theo môi trường (DB host, DEBUG...) sẽ được
    ghi đè ở local / production. Tách cấu hình để SQLite (local) và PostgreSQL (prod)
    cùng tồn tại, đồng thời cô lập secret ở phía production.
"""

from pathlib import Path

from dotenv import load_dotenv

# JA: BASE_DIR は backend/ を指す（このファイルから3つ上）。
# VI: BASE_DIR trỏ tới backend/ (lùi 3 cấp từ file này).
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# JA: リポジトリ直下の .env を読む。無ければ何もしない（本番は実環境変数を使う）。
# VI: Nạp .env ở gốc repo. Nếu không có thì bỏ qua (prod dùng biến môi trường thật).
load_dotenv(BASE_DIR.parent / ".env")

# JA: SECRET_KEY はデフォルトを持たせ、production では必ず環境変数で上書きする。
# VI: SECRET_KEY có giá trị mặc định; ở production BẮT BUỘC ghi đè bằng biến môi trường.
import os  # noqa: E402

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-insecure-key-change-me")

# JA: DEBUG / ALLOWED_HOSTS は環境ごとに変わるので local / production で設定する。
# VI: DEBUG / ALLOWED_HOSTS thay đổi theo môi trường -> đặt ở local / production.
DEBUG = False
ALLOWED_HOSTS: list[str] = []

# --- アプリ登録 / Đăng ký app ---
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "corsheaders",
]

# JA: 自作アプリは apps.<name> のフルパスで登録する（apps/ 配下に置くため）。
# VI: App tự viết đăng ký bằng đường dẫn đầy đủ apps.<name> (vì nằm trong apps/).
LOCAL_APPS = [
    "apps.common",
    "apps.accounts",
    "apps.ai",
    "apps.chat",
    "apps.topics",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    # JA: CORS は最上段に置くのが公式推奨（他 MW より先にヘッダを付与）。
    # VI: CORS đặt trên cùng theo khuyến nghị chính thức (gắn header trước các MW khác).
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# --- 認証 / Xác thực ---
# JA: カスタム User を使う。プロジェクト初期に必ず設定する（後からの変更は困難）。
# VI: Dùng User tùy biến. Phải đặt ngay từ đầu dự án (đổi sau rất khó).
AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- DRF ---
# JA: 認証はセッション方式（JWTは使わない）。全 API は既定でログイン必須にし、
#     公開が必要な view だけ個別に緩める（安全側の既定）。
# VI: Xác thực bằng session (không dùng JWT). Mọi API mặc định yêu cầu đăng nhập,
#     chỉ nới lỏng riêng cho view cần công khai (mặc định thiên về an toàn).
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "EXCEPTION_HANDLER": "apps.common.exceptions.drf_exception_handler",
}

# --- 国際化 / Quốc tế hóa ---
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Tokyo"
USE_I18N = True
USE_TZ = True

# --- 静的ファイル / Static ---
STATIC_URL = "static/"

# JA: 主キーの既定は BigAutoField。ただし独自モデルは common.BaseModel で UUID を使う。
# VI: Khóa chính mặc định là BigAutoField. Model tự viết dùng UUID qua common.BaseModel.
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
