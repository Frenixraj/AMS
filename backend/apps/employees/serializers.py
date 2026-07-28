"""Serializers for departments and employees."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers

from employees.models import Department, Employee
from notifications.models import Notification
from notifications.services import notify_admins_and_managers

User = get_user_model()


class DepartmentSerializer(serializers.ModelSerializer):
    manager_email = serializers.EmailField(source="manager.email", read_only=True, default=None)
    employee_count = serializers.SerializerMethodField()

    class Meta:
        model = Department
        fields = (
            "id",
            "name",
            "code",
            "description",
            "manager",
            "manager_email",
            "employee_count",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at", "employee_count")

    def get_employee_count(self, obj: Department) -> int:
        if hasattr(obj, "_employee_count"):
            return obj._employee_count
        return obj.employees.count()

    def validate_code(self, value: str) -> str:
        return value.strip().upper()


class EmployeeSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", read_only=True)
    full_name = serializers.SerializerMethodField()
    department_name = serializers.CharField(source="department.name", read_only=True)
    user_role = serializers.CharField(source="user.role", read_only=True)

    class Meta:
        model = Employee
        fields = (
            "id",
            "user",
            "email",
            "full_name",
            "user_role",
            "department",
            "department_name",
            "employee_code",
            "job_title",
            "phone",
            "hire_date",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def get_full_name(self, obj: Employee) -> str:
        name = f"{obj.user.first_name} {obj.user.last_name}".strip()
        return name or obj.user.email

    def validate_employee_code(self, value: str) -> str:
        return value.strip().upper()

    def validate_user(self, user):
        qs = Employee.objects.filter(user=user)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("This user already has an employee profile.")
        return user

    def create(self, validated_data):
        employee = super().create(validated_data)
        notify_admins_and_managers(
            title="New employee added",
            message=(
                f"{employee.employee_code} linked to {employee.user.email} "
                f"in {employee.department.name}."
            ),
            notification_type=Notification.NotificationType.INFO,
            link="/employees",
            entity_type="employees.Employee",
            entity_id=employee.id,
        )
        return employee


class EmployeeProvisionSerializer(serializers.Serializer):
    """Create a login user + employee profile in one step."""

    email = serializers.EmailField()
    password = serializers.CharField(min_length=8, write_only=True)
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True, default="")
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True, default="")
    role = serializers.ChoiceField(
        choices=["EMPLOYEE", "MANAGER", "IT_TEAM", "ADMIN"],
        default="EMPLOYEE",
    )
    department = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.filter(is_active=True)
    )
    employee_code = serializers.CharField(max_length=32)
    job_title = serializers.CharField(max_length=120, required=False, allow_blank=True, default="")
    phone = serializers.CharField(max_length=32, required=False, allow_blank=True, default="")

    def validate_email(self, value: str) -> str:
        email = value.strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return email

    def validate_employee_code(self, value: str) -> str:
        code = value.strip().upper()
        if Employee.objects.filter(employee_code__iexact=code).exists():
            raise serializers.ValidationError("Employee code already in use.")
        return code

    @transaction.atomic
    def create(self, validated_data):
        email = validated_data["email"]
        username = email.split("@")[0][:100]
        base = username
        n = 1
        while User.objects.filter(username=username).exists():
            username = f"{base}{n}"
            n += 1

        user = User.objects.create_user(
            username=username,
            email=email,
            password=validated_data["password"],
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
            role=validated_data.get("role", User.Role.EMPLOYEE),
        )
        employee = Employee.objects.create(
            user=user,
            department=validated_data["department"],
            employee_code=validated_data["employee_code"],
            job_title=validated_data.get("job_title", ""),
            phone=validated_data.get("phone", ""),
        )
        notify_admins_and_managers(
            title="New employee added",
            message=(
                f"{employee.employee_code} ({email}) created in "
                f"{employee.department.name} with role {user.role}."
            ),
            notification_type=Notification.NotificationType.INFO,
            link="/employees",
            entity_type="employees.Employee",
            entity_id=employee.id,
        )
        return employee
