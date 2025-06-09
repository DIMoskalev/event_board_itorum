from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .apps import NotificationsConfig
from .views import NotificationViewSet

app_name = NotificationsConfig.name

router = DefaultRouter()
router.register("", NotificationViewSet, basename="notifications")

urlpatterns = [
    path("", include(router.urls)),
]
