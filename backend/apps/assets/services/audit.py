"""Asset-specific audit helpers."""

from __future__ import annotations

from typing import Any

from django.http import HttpRequest

from assets.models import Asset
from common.models import AuditLog
from common.utils import write_audit_log

ASSET_ENTITY_TYPE = "assets.Asset"


def _snapshot(asset: Asset) -> dict[str, Any]:
    return {
        "asset_tag": asset.asset_tag,
        "name": asset.name,
        "category_id": asset.category_id,
        "brand": asset.brand,
        "model": asset.model,
        "serial_number": asset.serial_number,
        "status": asset.status,
        "vendor_id": asset.vendor_id,
        "purchase_date": str(asset.purchase_date) if asset.purchase_date else None,
        "purchase_cost": str(asset.purchase_cost) if asset.purchase_cost is not None else None,
        "warranty_expiry": str(asset.warranty_expiry) if asset.warranty_expiry else None,
    }


def log_asset_change(
    *,
    actor,
    action: str,
    asset: Asset,
    before: dict[str, Any] | None = None,
    after: dict[str, Any] | None = None,
    request: HttpRequest | None = None,
) -> AuditLog:
    changes: dict[str, Any] = {}
    if before is not None:
        changes["before"] = before
    if after is not None:
        changes["after"] = after
    elif action == AuditLog.Action.CREATE:
        changes["after"] = _snapshot(asset)

    return write_audit_log(
        actor=actor,
        action=action,
        entity_type=ASSET_ENTITY_TYPE,
        entity_id=asset.pk,
        changes=changes,
        request=request,
    )


def asset_snapshot(asset: Asset) -> dict[str, Any]:
    return _snapshot(asset)
