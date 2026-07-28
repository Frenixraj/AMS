"""Email helpers — console/log in DEV, real SMTP when configured."""

from __future__ import annotations

import logging
from typing import Any

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger("assetflow.email")


def send_email_placeholder(
    *,
    to_email: str,
    subject: str,
    body: str,
    context: dict[str, Any] | None = None,
) -> None:
    """
    Send email when EMAIL_HOST is set; otherwise log for local verification.
    """
    logger.info(
        "EMAIL | to=%s | subject=%s | context=%s | body=%s",
        to_email,
        subject,
        context or {},
        body,
    )
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "assetflow@localhost")
    try:
        send_mail(
            subject=subject,
            message=body,
            from_email=from_email,
            recipient_list=[to_email],
            fail_silently=True,
        )
    except Exception:
        logger.exception("Failed to send email to %s", to_email)


def notify_admin_mailbox(*, subject: str, body: str, context: dict[str, Any] | None = None) -> None:
    """Always notify the configured admin mailbox (default frenixraj@gmail.com)."""
    admin_email = getattr(settings, "ADMIN_NOTIFY_EMAIL", "frenixraj@gmail.com")
    send_email_placeholder(
        to_email=admin_email,
        subject=subject,
        body=body,
        context=context,
    )
