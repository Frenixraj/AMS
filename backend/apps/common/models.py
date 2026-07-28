"""
Shared abstract base models and cross-cutting persistence (AuditLog).
"""

from django.conf import settings
from django.db import models


class TimeStampedModel(models.Model):
    """Abstract base: created_at / updated_at on every concrete table that inherits it."""

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class AuditLog(TimeStampedModel):
    """
    Immutable-style audit trail for domain mutations.
    entity_type + entity_id identify the target row without polymorphic FKs.
    """

    class Action(models.TextChoices):
        CREATE = "CREATE", "Create"
        UPDATE = "UPDATE", "Update"
        DELETE = "DELETE", "Delete"
        ASSIGN = "ASSIGN", "Assign"
        RETURN = "RETURN", "Return"
        APPROVE = "APPROVE", "Approve"
        REJECT = "REJECT", "Reject"
        LOGIN = "LOGIN", "Login"
        STATUS_CHANGE = "STATUS_CHANGE", "Status Change"

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
        help_text="User who performed the action; null for system jobs.",
    )
    action = models.CharField(max_length=32, choices=Action.choices, db_index=True)
    entity_type = models.CharField(
        max_length=64,
        db_index=True,
        help_text="Model label, e.g. 'assets.Asset'.",
    )
    entity_id = models.CharField(
        max_length=64,
        db_index=True,
        help_text="Primary key of the target entity as string.",
    )
    changes = models.JSONField(
        default=dict,
        blank=True,
        help_text="Before/after snapshot or field diffs.",
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=512, blank=True, default="")

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["entity_type", "entity_id"], name="idx_audit_entity"),
            models.Index(fields=["actor", "created_at"], name="idx_audit_actor_created"),
            models.Index(fields=["action", "created_at"], name="idx_audit_action_created"),
        ]
        verbose_name = "audit log"
        verbose_name_plural = "audit logs"

    def __str__(self) -> str:
        return f"{self.action} {self.entity_type}:{self.entity_id}"
