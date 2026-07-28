"""Dashboard analytics aggregation."""

from __future__ import annotations

from calendar import month_abbr
from datetime import timedelta
from typing import Any

from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.utils import timezone

from assets.models import Asset, AssetAssignment
from common.models import AuditLog


def _status_counts() -> dict[str, int]:
    rows = Asset.objects.values("status").annotate(count=Count("id"))
    by_status = {row["status"]: row["count"] for row in rows}
    total = sum(by_status.values())
    return {
        "total_assets": total,
        "allocated": by_status.get(Asset.Status.ALLOCATED, 0),
        "available": by_status.get(Asset.Status.AVAILABLE, 0),
        "maintenance": by_status.get(Asset.Status.MAINTENANCE, 0),
        "lost": by_status.get(Asset.Status.LOST, 0),
        "requested": by_status.get(Asset.Status.REQUESTED, 0),
        "retired": by_status.get(Asset.Status.RETIRED, 0),
    }


def _warranty_expiring(within_days: int = 90) -> int:
    today = timezone.localdate()
    horizon = today + timedelta(days=within_days)
    return Asset.objects.filter(
        warranty_expiry__isnull=False,
        warranty_expiry__gte=today,
        warranty_expiry__lte=horizon,
    ).exclude(
        status__in=[Asset.Status.RETIRED, Asset.Status.LOST],
    ).count()


def _category_distribution() -> list[dict[str, Any]]:
    rows = (
        Asset.objects.values("category__name")
        .annotate(value=Count("id"))
        .order_by("-value", "category__name")
    )
    return [
        {"name": row["category__name"] or "Uncategorized", "value": row["value"]}
        for row in rows
    ]


def _department_distribution() -> list[dict[str, Any]]:
    """Active allocations grouped by employee department."""
    rows = (
        AssetAssignment.objects.filter(status=AssetAssignment.Status.ACTIVE)
        .values("employee__department__name")
        .annotate(value=Count("id"))
        .order_by("-value", "employee__department__name")
    )
    return [
        {
            "name": row["employee__department__name"] or "Unassigned",
            "value": row["value"],
        }
        for row in rows
    ]


def _monthly_allocations(months: int = 12) -> list[dict[str, Any]]:
    """Assignment counts for the last N calendar months (including empty months)."""
    now = timezone.now()
    start = (now.replace(day=1) - timedelta(days=32 * (months - 1))).replace(day=1)

    rows = (
        AssetAssignment.objects.filter(assigned_at__gte=start)
        .annotate(month=TruncMonth("assigned_at"))
        .values("month")
        .annotate(count=Count("id"))
        .order_by("month")
    )
    by_month = {
        row["month"].date().replace(day=1): row["count"]
        for row in rows
        if row["month"] is not None
    }

    # Walk months forward from start to current month.
    cursor = start.date().replace(day=1)
    end = now.date().replace(day=1)
    series: list[dict[str, Any]] = []
    while cursor <= end:
        series.append(
            {
                "month": f"{month_abbr[cursor.month]} {cursor.year}",
                "month_key": cursor.isoformat(),
                "allocations": by_month.get(cursor, 0),
            }
        )
        if cursor.month == 12:
            cursor = cursor.replace(year=cursor.year + 1, month=1)
        else:
            cursor = cursor.replace(month=cursor.month + 1)
    # Keep only the last N months if we overshot
    return series[-months:]


def _recent_activities(limit: int = 15) -> list[dict[str, Any]]:
    logs = (
        AuditLog.objects.select_related("actor")
        .order_by("-created_at")[:limit]
    )
    return [
        {
            "id": log.id,
            "action": log.action,
            "entity_type": log.entity_type,
            "entity_id": log.entity_id,
            "actor_email": log.actor.email if log.actor else None,
            "changes": log.changes,
            "created_at": log.created_at,
        }
        for log in logs
    ]


def build_dashboard_summary(*, warranty_days: int = 90) -> dict[str, Any]:
    widgets = _status_counts()
    widgets["warranty_expiring"] = _warranty_expiring(warranty_days)
    widgets["warranty_window_days"] = warranty_days

    return {
        "widgets": widgets,
        "charts": {
            "category_distribution": _category_distribution(),
            "department_distribution": _department_distribution(),
            "monthly_allocations": _monthly_allocations(12),
        },
        "recent_activities": _recent_activities(15),
        "generated_at": timezone.now(),
    }
