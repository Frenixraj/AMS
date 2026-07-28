"""
Custom User model for AssetFlow role-based access.
Must be set as AUTH_USER_MODEL before the first migration.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models

from common.models import TimeStampedModel


class User(AbstractUser, TimeStampedModel):
    """
    Application user. Role drives API permissions.
    Employee profile (HR details) lives in employees.Employee (1:1).
    """

    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        IT_TEAM = "IT_TEAM", "IT Team"
        MANAGER = "MANAGER", "Manager"
        EMPLOYEE = "EMPLOYEE", "Employee"

    email = models.EmailField(unique=True)
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.EMPLOYEE,
        db_index=True,
    )

    # Prefer email for login while keeping username for Django admin uniqueness.
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        ordering = ["email"]
        indexes = [
            models.Index(fields=["role", "is_active"], name="idx_user_role_active"),
        ]
        verbose_name = "user"
        verbose_name_plural = "users"

    def __str__(self) -> str:
        return f"{self.email} ({self.role})"
