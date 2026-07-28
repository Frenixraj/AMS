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
    Profile fields live on the user so Admin / Asset Manager also have them.
    Optional HR linkage: employees.Employee (1:1).
    """

    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        ASSET_MANAGER = "ASSET_MANAGER", "Asset Manager"
        MANAGER = "MANAGER", "Manager"
        EMPLOYEE = "EMPLOYEE", "Employee"
        # Legacy — migrated to ASSET_MANAGER; kept so old rows remain valid until migrated.
        IT_TEAM = "IT_TEAM", "IT Team (legacy)"

    email = models.EmailField(unique=True)
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.EMPLOYEE,
        db_index=True,
    )
    phone = models.CharField(max_length=32, blank=True, default="")
    address = models.TextField(blank=True, default="")
    profile_picture = models.ImageField(
        upload_to="profiles/%Y/%m/",
        blank=True,
        null=True,
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
        constraints = [
            models.UniqueConstraint(
                fields=["role"],
                condition=models.Q(role="ASSET_MANAGER", is_active=True),
                name="uq_one_active_asset_manager",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.email} ({self.role})"

    @property
    def is_asset_ops(self) -> bool:
        """Admin or Asset Manager (includes legacy IT_TEAM)."""
        if self.is_superuser:
            return True
        return self.role in (
            self.Role.ADMIN,
            self.Role.ASSET_MANAGER,
            self.Role.IT_TEAM,
        )
