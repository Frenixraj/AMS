"""Notification package public API."""

from notifications.services.email import send_email_placeholder
from notifications.services.notify import notify_user

__all__ = ["notify_user", "send_email_placeholder"]
