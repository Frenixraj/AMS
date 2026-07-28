"""Broadcast helpers for role-targeted notifications."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.db.models import Q

from notifications.models import Notification
from notifications.services.notify import notify_user

User = get_user_model()


def notify_admins_and_managers(
    *,
    title: str,
    message: str,
    notification_type: str = Notification.NotificationType.INFO,
    link: str = "",
    entity_type: str = "",
    entity_id: str | int = "",
    exclude_user_id: int | None = None,
) -> int:
    """
    Notify every active Admin and Manager (and superusers).
    Returns number of notifications created.
    """
    qs = User.objects.filter(is_active=True).filter(
        Q(role__in=["ADMIN", "MANAGER"]) | Q(is_superuser=True)
    )
    if exclude_user_id is not None:
        qs = qs.exclude(pk=exclude_user_id)

    count = 0
    for recipient in qs.distinct():
        notify_user(
            recipient=recipient,
            title=title,
            message=message,
            notification_type=notification_type,
            link=link,
            entity_type=entity_type,
            entity_id=entity_id,
        )
        count += 1
    return count
