#!/usr/bin/env python
"""
manage.py
JA: Django のコマンド入口。既定の設定は config.settings.local。
    本番系コマンドは DJANGO_SETTINGS_MODULE=config.settings.production を指定して実行する。
VI: Điểm vào lệnh Django. Cấu hình mặc định là config.settings.local.
    Lệnh cho production chạy kèm DJANGO_SETTINGS_MODULE=config.settings.production.
"""

import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Django をインポートできません。仮想環境を有効化しましたか？ / "
            "Không import được Django. Bạn đã kích hoạt virtualenv chưa?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
