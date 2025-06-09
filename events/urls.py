from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .apps import EventsConfig
from .views import EventViewSet, TagViewSet

app_name = EventsConfig.name

router = DefaultRouter()
router.register("events", EventViewSet, basename="events")
router.register("tags", TagViewSet, basename="tags")

urlpatterns = [
    path("", include(router.urls)),
]
