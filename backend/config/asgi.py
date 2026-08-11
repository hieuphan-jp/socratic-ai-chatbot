"""
config/asgi.py
JA: 非同期サーバ向けの ASGI 入口。将来 WebSocket 等を使う担当のための受け皿。
VI: Điểm vào ASGI cho server bất đồng bộ. Chỗ dành cho WebSocket... sau này.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

application = get_asgi_application()
