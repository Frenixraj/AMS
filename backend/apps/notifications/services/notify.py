"""In-app + email notification helpers."""

from __future__ import annotations

from typing import Any

from notifications.models import Notification
from notifications.services.email import send_email_placeholder


def notify_user(
    *,
    recipient,
    title: str,
    message: str,
    notification_type: str = Notification.NotificationType.INFO,
    link: str = "",
    entity_type: str = "",
    entity_id: str | int = "",
    email_subject: str | None = None,
    email_context: dict[str, Any] | None = None,
) -> Notification:
    """Create an in-app notification and emit an email placeholder."""
    notification = Notification.objects.create(
        recipient=recipient,
        title=title,
        message=message,
        notification_type=notification_type,
        link=link,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id != "" else "",
    )

    send_email_placeholder(
        to_email=recipient.email,
        subject=email_subject or title,
        body=message,
        context={
            "notification_id": notification.id,
            "link": link,
            "entity_type": entity_type,
            "entity_id": str(entity_id) if entity_id != "" else "",
            **(email_context or {}),
        },
    )
    return notification
