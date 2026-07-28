from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("health/", views.health_check, name="health"),
    path("summary/", views.summary, name="summary"),
]
