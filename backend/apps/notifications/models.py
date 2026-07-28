"""
In-app notifications for users.
"""

from django.conf import settings
from django.db import models

from common.models import TimeStampedModel


class Notification(TimeStampedModel):
    """Per-user notification (request updates, assignments, maintenance, …)."""

    class NotificationType(models.TextChoices):
        INFO = "INFO", "Info"
        REQUEST = "REQUEST", "Request"
        APPROVAL = "APPROVAL", "Approval"
        ASSIGNMENT = "ASSIGNMENT", "Assignment"
        MAINTENANCE = "MAINTENANCE", "Maintenance"
        SYSTEM = "SYSTEM", "System"

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    title = models.CharField(max_length=160)
    message = models.TextField()
    notification_type = models.CharField(
        max_length=20,
        choices=NotificationType.choices,
        default=NotificationType.INFO,
        db_index=True,
    )
    is_read = models.BooleanField(default=False, db_index=True)
    link = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Optional deep link path in the SPA, e.g. /requests/42.",
    )
    # Optional polymorphic target without hard FKs to every domain table.
    entity_type = models.CharField(max_length=64, blank=True, default="")
    entity_id = models.CharField(max_length=64, blank=True, default="")

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["recipient", "is_read", "created_at"],
                name="idx_notif_recipient_read",
            ),
            models.Index(
                fields=["notification_type", "created_at"],
                name="idx_notif_type_created",
            ),
        ]
        verbose_name = "notification"
        verbose_name_plural = "notifications"

    def __str__(self) -> str:
        return f"To {self.recipient_id}: {self.title}"
