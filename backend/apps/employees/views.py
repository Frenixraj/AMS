"""API views for departments and employees."""

from django.db.models import Count
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from common.permissions import IsAdminOrITTeam, IsAdminOrITTeamOrReadOnly
from employees.filters import DepartmentFilter, EmployeeFilter
from employees.models import Department, Employee
from employees.serializers import (
    DepartmentSerializer,
    EmployeeProvisionSerializer,
    EmployeeSerializer,
)


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    return Response({"status": "ok", "app": "employees"})


class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.select_related("manager").annotate(
        _employee_count=Count("employees")
    )
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated, IsAdminOrITTeamOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = DepartmentFilter
    search_fields = ("name", "code", "description")
    ordering_fields = ("name", "code", "created_at")
    ordering = ("name",)


class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.select_related("user", "department").all()
    serializer_class = EmployeeSerializer
    permission_classes = [IsAuthenticated, IsAdminOrITTeamOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = EmployeeFilter
    search_fields = (
        "employee_code",
        "job_title",
        "phone",
        "user__email",
        "user__first_name",
        "user__last_name",
    )
    ordering_fields = ("employee_code", "hire_date", "created_at")
    ordering = ("employee_code",)

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.role == "MANAGER" and not user.is_superuser:
            return qs.filter(department__manager=user)
        if user.role == "EMPLOYEE" and hasattr(user, "employee_profile"):
            if self.action in ("list", "retrieve"):
                return qs.filter(pk=user.employee_profile.pk)
        return qs

    @action(
        detail=False,
        methods=["post"],
        url_path="provision",
        permission_classes=[IsAuthenticated, IsAdminOrITTeam],
    )
    def provision(self, request):
        """Create user login + employee profile together."""
        serializer = EmployeeProvisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        employee = serializer.save()
        return Response(
            EmployeeSerializer(employee).data,
            status=status.HTTP_201_CREATED,
        )
