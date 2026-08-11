# JA: ルーティング定義 / VI: Định nghĩa router
from rest_framework.routers import DefaultRouter

from .views import ChatSessionViewSet

router = DefaultRouter()
router.register("chat-sessions", ChatSessionViewSet, basename="chat-session")

urlpatterns = router.urls
