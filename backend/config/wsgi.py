"""
config/wsgi.py
JA: 同期サーバ(gunicorn等)向けの WSGI 入口。既定は local 設定。
VI: Điểm vào WSGI cho server đồng bộ (gunicorn...). Mặc định dùng cấu hình local.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

application = get_wsgi_application()
