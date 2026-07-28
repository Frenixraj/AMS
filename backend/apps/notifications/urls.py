from django.urls import include, path
from rest_framework.routers import DefaultRouter

from notifications.views import NotificationViewSet, health_check

router = DefaultRouter()
router.register(r"", NotificationViewSet, basename="notification")

app_name = "notifications"

urlpatterns = [
    path("health/", health_check, name="health"),
    path("", include(router.urls)),
]
