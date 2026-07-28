"""Serializers for departments and employees."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from rest_framework import serializers

from employees.models import Department, Employee

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
