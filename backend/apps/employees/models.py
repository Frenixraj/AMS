"""
Organization structure: departments and employee profiles.
"""

from django.conf import settings
from django.db import models

from common.models import TimeStampedModel


class Department(TimeStampedModel):
    """Organizational unit. Managers oversee department asset requests."""

    name = models.CharField(max_length=120, unique=True)
    code = models.CharField(max_length=32, unique=True)
    description = models.TextField(blank=True, default="")
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="managed_departments",
        limit_choices_to={"role__in": ["MANAGER", "ADMIN"]},
        help_text="Optional department manager (User with MANAGER/ADMIN role).",
    )
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["is_active", "name"], name="idx_dept_active_name"),
        ]
        verbose_name = "department"
        verbose_name_plural = "departments"

    def __str__(self) -> str:
        return f"{self.code} — {self.name}"


class Employee(TimeStampedModel):
    """
    HR/profile record linked 1:1 to a login User.
    Separates auth credentials from employment attributes (3NF).
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="employee_profile",
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name="employees",
    )
    employee_code = models.CharField(max_length=32, unique=True)
    job_title = models.CharField(max_length=120, blank=True, default="")
    phone = models.CharField(max_length=32, blank=True, default="")
    hire_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ["employee_code"]
        indexes = [
            models.Index(fields=["department", "is_active"], name="idx_emp_dept_active"),
        ]
        verbose_name = "employee"
        verbose_name_plural = "employees"

    def __str__(self) -> str:
        return f"{self.employee_code} ({self.user.email})"
