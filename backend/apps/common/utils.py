"""Shared backend utilities."""

from __future__ import annotations

from typing import Any

from django.http import HttpRequest

from common.models import AuditLog


def get_client_ip(request: HttpRequest | None) -> str | None:
    if request is None:
        return None
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def write_audit_log(
    *,
    actor,
    action: str,
    entity_type: str,
    entity_id: str | int,
    changes: dict[str, Any] | None = None,
    request: HttpRequest | None = None,
) -> AuditLog:
    """Persist an audit trail entry for a domain mutation."""
    user_agent = ""
    if request is not None:
        user_agent = (request.META.get("HTTP_USER_AGENT") or "")[:512]

    return AuditLog.objects.create(
        actor=actor if getattr(actor, "is_authenticated", False) else None,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id),
        changes=changes or {},
        ip_address=get_client_ip(request),
        user_agent=user_agent,
    )
