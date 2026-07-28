from django.urls import include, path
from rest_framework.routers import DefaultRouter

from employees.views import DepartmentViewSet, EmployeeViewSet, health_check

router = DefaultRouter()
router.register(r"departments", DepartmentViewSet, basename="department")
router.register(r"", EmployeeViewSet, basename="employee")

app_name = "employees"

urlpatterns = [
    path("health/", health_check, name="health"),
    path("", include(router.urls)),
]
