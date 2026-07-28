"""API views for departments and employees."""

from django.db.models import Count
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from common.permissions import (
    IsAdminOrAssetManagerOrReadOnly,
    IsAdminOrAssetManager,
    _role,
    is_asset_ops_role,
)
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
    permission_classes = [IsAuthenticated, IsAdminOrAssetManagerOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = DepartmentFilter
    search_fields = ("name", "code", "description")
    ordering_fields = ("name", "code", "created_at")
    ordering = ("name",)

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if _role(user) == "MANAGER":
            return qs.filter(manager=user)
        return qs


class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.select_related("user", "department").all()
    serializer_class = EmployeeSerializer
    permission_classes = [IsAuthenticated, IsAdminOrAssetManagerOrReadOnly]
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
        role = _role(user)
        if role == "MANAGER":
            return qs.filter(department__manager=user)
        if role == "EMPLOYEE" and hasattr(user, "employee_profile"):
            if self.action in ("list", "retrieve"):
                return qs.filter(pk=user.employee_profile.pk)
        return qs

    def get_permissions(self):
        # Managers may create/provision within their department
        if self.action in ("create", "provision", "partial_update", "update"):
            return [IsAuthenticated()]
        return super().get_permissions()

    def perform_create(self, serializer):
        user = self.request.user
        role = _role(user)
        if is_asset_ops_role(role) or role == "ADMIN":
            serializer.save()
            return
        if role == "MANAGER":
            dept = serializer.validated_data.get("department")
            if not dept or dept.manager_id != user.id:
                raise PermissionDenied("Managers may only add employees to their department.")
            serializer.save()
            return
        raise PermissionDenied("Not allowed to create employees.")

    @action(
        detail=False,
        methods=["post"],
        url_path="provision",
    )
    def provision(self, request):
        """Create user login + employee profile together."""
        role = _role(request.user)
        serializer = EmployeeProvisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if role == "MANAGER":
            dept = serializer.validated_data["department"]
            if dept.manager_id != request.user.id:
                raise PermissionDenied("Managers may only add employees to their department.")
            # Managers can only create EMPLOYEE role accounts
            serializer.validated_data["role"] = "EMPLOYEE"
        elif not (is_asset_ops_role(role) or role == "ADMIN"):
            raise PermissionDenied("Not allowed.")

        employee = serializer.save()
        return Response(
            EmployeeSerializer(employee).data,
            status=status.HTTP_201_CREATED,
        )
