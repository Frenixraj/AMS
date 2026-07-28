"""Report dataset builders (shared by Excel and PDF exporters)."""

from __future__ import annotations

from typing import Any

from django.db.models import Count

from assets.models import Asset, AssetAssignment
from maintenance.models import MaintenanceRecord


def assets_by_department_rows() -> list[dict[str, Any]]:
    """
    Currently allocated assets with holding department.
    Unallocated assets are omitted from this departmental view.
    """
    qs = (
        AssetAssignment.objects.filter(status=AssetAssignment.Status.ACTIVE)
        .select_related(
            "asset",
            "asset__category",
            "employee",
            "employee__user",
            "employee__department",
        )
        .order_by("employee__department__name", "asset__asset_tag")
    )
    return [
        {
            "department": a.employee.department.name,
            "department_code": a.employee.department.code,
            "asset_tag": a.asset.asset_tag,
            "asset_name": a.asset.name,
            "category": a.asset.category.name,
            "status": a.asset.status,
            "employee_code": a.employee.employee_code,
            "employee_email": a.employee.user.email,
            "assigned_at": a.assigned_at.isoformat(sep=" ", timespec="minutes"),
        }
        for a in qs
    ]


def assets_by_department_summary() -> list[dict[str, Any]]:
    rows = (
        AssetAssignment.objects.filter(status=AssetAssignment.Status.ACTIVE)
        .values("employee__department__name", "employee__department__code")
        .annotate(count=Count("id"))
        .order_by("-count", "employee__department__name")
    )
    return [
        {
            "department": r["employee__department__name"] or "Unassigned",
            "department_code": r["employee__department__code"] or "",
            "asset_count": r["count"],
        }
        for r in rows
    ]


def assets_by_person_rows() -> list[dict[str, Any]]:
    """Active allocations grouped for per-person reporting."""
    qs = (
        AssetAssignment.objects.filter(status=AssetAssignment.Status.ACTIVE)
        .select_related(
            "asset",
            "asset__category",
            "employee",
            "employee__user",
            "employee__department",
        )
        .order_by("employee__employee_code", "asset__asset_tag")
    )
    return [
        {
            "employee_id": a.employee_id,
            "employee_code": a.employee.employee_code,
            "employee_name": (
                f"{a.employee.user.first_name} {a.employee.user.last_name}".strip()
                or a.employee.user.email
            ),
            "employee_email": a.employee.user.email,
            "department": a.employee.department.name,
            "department_code": a.employee.department.code,
            "asset_id": a.asset_id,
            "asset_tag": a.asset.asset_tag,
            "asset_name": a.asset.name,
            "category": a.asset.category.name,
            "status": a.asset.status,
            "assigned_at": a.assigned_at.isoformat(sep=" ", timespec="minutes"),
        }
        for a in qs
    ]


def assets_by_person_summary() -> list[dict[str, Any]]:
    rows = (
        AssetAssignment.objects.filter(status=AssetAssignment.Status.ACTIVE)
        .values(
            "employee_id",
            "employee__employee_code",
            "employee__user__email",
            "employee__user__first_name",
            "employee__user__last_name",
            "employee__department__name",
        )
        .annotate(asset_count=Count("id"))
        .order_by("-asset_count", "employee__employee_code")
    )
    result = []
    for r in rows:
        name = f"{r['employee__user__first_name']} {r['employee__user__last_name']}".strip()
        result.append(
            {
                "employee_id": r["employee_id"],
                "employee_code": r["employee__employee_code"],
                "employee_name": name or r["employee__user__email"],
                "employee_email": r["employee__user__email"],
                "department": r["employee__department__name"],
                "asset_count": r["asset_count"],
            }
        )
    return result


def assets_by_category_rows() -> list[dict[str, Any]]:
    qs = Asset.objects.select_related("category", "vendor").order_by(
        "category__name", "asset_tag"
    )
    return [
        {
            "category": a.category.name,
            "category_code": a.category.code,
            "asset_tag": a.asset_tag,
            "asset_name": a.name,
            "status": a.status,
            "serial_number": a.serial_number,
            "brand": a.brand,
            "model": a.model,
            "vendor": a.vendor.name if a.vendor else "",
            "purchase_cost": str(a.purchase_cost) if a.purchase_cost is not None else "",
        }
        for a in qs
    ]


def assets_by_category_summary() -> list[dict[str, Any]]:
    rows = (
        Asset.objects.values("category__name", "category__code")
        .annotate(count=Count("id"))
        .order_by("-count", "category__name")
    )
    return [
        {
            "category": r["category__name"],
            "category_code": r["category__code"],
            "asset_count": r["count"],
        }
        for r in rows
    ]


def allocation_history_rows() -> list[dict[str, Any]]:
    qs = (
        AssetAssignment.objects.select_related(
            "asset",
            "employee",
            "employee__user",
            "employee__department",
            "assigned_by",
        )
        .order_by("-assigned_at")
    )
    return [
        {
            "asset_tag": a.asset.asset_tag,
            "asset_name": a.asset.name,
            "employee_code": a.employee.employee_code,
            "employee_email": a.employee.user.email,
            "department": a.employee.department.name,
            "status": a.status,
            "assigned_at": a.assigned_at.isoformat(sep=" ", timespec="minutes"),
            "returned_at": (
                a.returned_at.isoformat(sep=" ", timespec="minutes")
                if a.returned_at
                else ""
            ),
            "assigned_by": a.assigned_by.email if a.assigned_by else "",
            "notes": a.notes,
        }
        for a in qs
    ]


def maintenance_history_rows() -> list[dict[str, Any]]:
    qs = (
        MaintenanceRecord.objects.select_related(
            "asset",
            "reported_by",
            "reported_by__user",
            "assigned_to",
        )
        .order_by("-created_at")
    )
    return [
        {
            "asset_tag": m.asset.asset_tag,
            "asset_name": m.asset.name,
            "title": m.title,
            "status": m.status,
            "reported_by": m.reported_by.employee_code,
            "assigned_to": m.assigned_to.email if m.assigned_to else "",
            "cost": str(m.cost) if m.cost is not None else "",
            "started_at": (
                m.started_at.isoformat(sep=" ", timespec="minutes")
                if m.started_at
                else ""
            ),
            "completed_at": (
                m.completed_at.isoformat(sep=" ", timespec="minutes")
                if m.completed_at
                else ""
            ),
            "created_at": m.created_at.isoformat(sep=" ", timespec="minutes"),
            "resolution_notes": m.resolution_notes,
        }
        for m in qs
    ]
