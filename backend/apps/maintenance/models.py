"""
Maintenance / issue tracking for assets.
"""

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from common.models import TimeStampedModel


class MaintenanceRecord(TimeStampedModel):
    """Repair, service, or issue report against an asset."""

    class Status(models.TextChoices):
        PENDING_APPROVAL = "PENDING_APPROVAL", "Pending Approval"
        OPEN = "OPEN", "Open"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"
        REJECTED = "REJECTED", "Rejected"

    asset = models.ForeignKey(
        "assets.Asset",
        on_delete=models.CASCADE,
        related_name="maintenance_records",
    )
    reported_by = models.ForeignKey(
        "employees.Employee",
        on_delete=models.PROTECT,
        related_name="reported_maintenance",
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_maintenance",
        limit_choices_to={"role__in": ["ASSET_MANAGER", "ADMIN", "IT_TEAM"]},
        help_text="Staff responsible for the ticket.",
    )
    title = models.CharField(max_length=160)
    issue_description = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING_APPROVAL,
        db_index=True,
    )
    approval_comments = models.TextField(blank=True, default="")
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="maintenance_decisions",
    )
    decided_at = models.DateTimeField(null=True, blank=True)
    cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["asset", "status"], name="idx_maint_asset_status"),
            models.Index(
                fields=["assigned_to", "status"],
                name="idx_maint_assignee_status",
            ),
            models.Index(
                fields=["reported_by", "created_at"],
                name="idx_maint_reporter_created",
            ),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(cost__isnull=True) | models.Q(cost__gte=0),
                name="chk_maint_cost_nonneg",
            ),
            models.CheckConstraint(
                check=(
                    models.Q(completed_at__isnull=True)
                    | models.Q(started_at__isnull=True)
                    | models.Q(completed_at__gte=models.F("started_at"))
                ),
                name="chk_maint_completed_after_start",
            ),
        ]
        verbose_name = "maintenance record"
        verbose_name_plural = "maintenance records"

    def __str__(self) -> str:
        return f"{self.asset.asset_tag}: {self.title} ({self.status})"
