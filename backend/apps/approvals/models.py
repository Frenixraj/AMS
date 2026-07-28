"""
Asset request and approval workflow models.
"""

from django.conf import settings
from django.db import models

from common.models import TimeStampedModel


class AssetRequest(TimeStampedModel):
    """
    Employee request for a new/specific asset.
    category and/or asset may be set depending on request type.
    """

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        CANCELLED = "CANCELLED", "Cancelled"
        FULFILLED = "FULFILLED", "Fulfilled"

    class Priority(models.TextChoices):
        LOW = "LOW", "Low"
        MEDIUM = "MEDIUM", "Medium"
        HIGH = "HIGH", "High"
        URGENT = "URGENT", "Urgent"

    request_number = models.CharField(max_length=32, unique=True)
    requested_by = models.ForeignKey(
        "employees.Employee",
        on_delete=models.PROTECT,
        related_name="asset_requests",
    )
    category = models.ForeignKey(
        "assets.AssetCategory",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="requests",
        help_text="Requested category when no specific asset is chosen.",
    )
    asset = models.ForeignKey(
        "assets.Asset",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="requests",
        help_text="Optional specific asset being requested.",
    )
    justification = models.TextField()
    priority = models.CharField(
        max_length=16,
        choices=Priority.choices,
        default=Priority.MEDIUM,
        db_index=True,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    fulfilled_at = models.DateTimeField(null=True, blank=True)
    fulfilled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="fulfilled_asset_requests",
        help_text="IT / Admin user who allocated the asset.",
    )
    assignment = models.ForeignKey(
        "assets.AssetAssignment",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="source_requests",
        help_text="Assignment created when the request was fulfilled.",
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["status", "priority", "created_at"],
                name="idx_req_status_prio_created",
            ),
            models.Index(
                fields=["requested_by", "status"],
                name="idx_req_employee_status",
            ),
        ]
        constraints = [
            # At least one of category or asset must be provided.
            models.CheckConstraint(
                check=models.Q(category__isnull=False) | models.Q(asset__isnull=False),
                name="chk_request_has_category_or_asset",
            ),
        ]
        verbose_name = "asset request"
        verbose_name_plural = "asset requests"

    def __str__(self) -> str:
        return f"{self.request_number} ({self.status})"


class Approval(TimeStampedModel):
    """
    Decision record for an AssetRequest.
    One approval row per request for the current single-step manager workflow.
    step supports future multi-level chains without schema redesign.
    """

    class Decision(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    asset_request = models.ForeignKey(
        AssetRequest,
        on_delete=models.CASCADE,
        related_name="approvals",
    )
    approver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="approvals_made",
        limit_choices_to={"role__in": ["MANAGER", "ADMIN"]},
        help_text="Assigned manager/admin. Null until a department manager is configured.",
    )
    step = models.PositiveSmallIntegerField(
        default=1,
        help_text="Approval level (1 = first approver).",
    )
    decision = models.CharField(
        max_length=20,
        choices=Decision.choices,
        default=Decision.PENDING,
        db_index=True,
    )
    comments = models.TextField(blank=True, default="")
    decided_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["asset_request_id", "step"]
        indexes = [
            models.Index(
                fields=["approver", "decision"],
                name="idx_approval_approver_decision",
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["asset_request", "step"],
                name="uq_approval_request_step",
            ),
            models.CheckConstraint(
                check=models.Q(step__gte=1),
                name="chk_approval_step_positive",
            ),
        ]
        verbose_name = "approval"
        verbose_name_plural = "approvals"

    def __str__(self) -> str:
        return f"{self.asset_request.request_number} step {self.step}: {self.decision}"
