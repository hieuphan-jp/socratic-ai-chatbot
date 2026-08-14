"""
JA: 間隔復習機能のルーティング登録。
VI: Đăng ký routing cho tính năng ôn tập ngắt quãng.
"""

from rest_framework.routers import DefaultRouter

from .views import ReviewScheduleViewSet

router = DefaultRouter()
router.register("review-schedules", ReviewScheduleViewSet, basename="review-schedule")
urlpatterns = router.urls

# config/urls.py に以下を1行追加すること:
#   path("api/", include("apps.reviews.urls"))
