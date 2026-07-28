"""Email notification placeholders (no real SMTP until configured)."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("assetflow.email")


def send_email_placeholder(
    *,
    to_email: str,
    subject: str,
    body: str,
    context: dict[str, Any] | None = None,
) -> None:
    """
    Placeholder for outbound email.

    Logs the intended message so workflow wiring can be verified in development.
    Replace the body of this function with Django `send_mail` / a provider
    once EMAIL_HOST settings are configured.
    """
    logger.info(
        "EMAIL_PLACEHOLDER | to=%s | subject=%s | context=%s | body=%s",
        to_email,
        subject,
        context or {},
        body,
    )
