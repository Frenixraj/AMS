from django.urls import include, path
from rest_framework.routers import DefaultRouter

from maintenance.views import MaintenanceRecordViewSet, health_check

router = DefaultRouter()
router.register(r"tickets", MaintenanceRecordViewSet, basename="maintenance-ticket")

app_name = "maintenance"

urlpatterns = [
    path("health/", health_check, name="health"),
    path("", include(router.urls)),
]
