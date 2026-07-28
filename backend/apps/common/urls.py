from django.urls import include, path

from common.audit_api import router as audit_router
from common import views

app_name = "common"

urlpatterns = [
    path("", views.health_check, name="health"),
]
