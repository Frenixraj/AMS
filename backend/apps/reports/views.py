"""Reports and export endpoints."""

from __future__ import annotations

import csv
import io
from datetime import timedelta

from django.db.models import Count
from django.http import HttpResponse
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from assets.models import Asset, AssetAssignment
from approvals.models import AssetRequest
from common.permissions import IsAdminOrITTeam
from reports.services import data as report_data
from reports.services.excel import (
    export_allocation_history_excel,
    export_assets_by_category_excel,
    export_assets_by_department_excel,
    export_maintenance_history_excel,
)
from reports.services.pdf import (
    export_allocation_history_pdf,
    export_assets_by_category_pdf,
    export_assets_by_department_pdf,
    export_maintenance_history_pdf,
)


def _file_response(content: bytes, *, filename: str, content_type: str) -> HttpResponse:
    response = HttpResponse(content, content_type=content_type)
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    return Response({"status": "ok", "app": "reports"})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def inventory_summary(request):
    """Asset inventory grouped by status and category."""
    by_status = list(
        Asset.objects.values("status").annotate(count=Count("id")).order_by("status")
    )
    by_category = list(
        Asset.objects.values("category__name", "status")
        .annotate(count=Count("id"))
        .order_by("category__name", "status")
    )
    return Response(
        {
            "by_status": by_status,
            "by_category": [
                {
                    "category": row["category__name"],
                    "status": row["status"],
                    "count": row["count"],
                }
                for row in by_category
            ],
            "total": Asset.objects.count(),
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def warranty_report(request):
    """Assets with warranty expiring within N days (default 90)."""
    try:
        days = int(request.query_params.get("days", 90))
    except (TypeError, ValueError):
        days = 90
    today = timezone.localdate()
    horizon = today + timedelta(days=max(1, min(days, 365)))
    assets = (
        Asset.objects.filter(
            warranty_expiry__isnull=False,
            warranty_expiry__gte=today,
            warranty_expiry__lte=horizon,
        )
        .exclude(status__in=[Asset.Status.RETIRED, Asset.Status.LOST])
        .select_related("category", "vendor")
        .order_by("warranty_expiry")
    )
    data = [
        {
            "id": a.id,
            "asset_tag": a.asset_tag,
            "name": a.name,
            "category": a.category.name,
            "status": a.status,
            "warranty_expiry": a.warranty_expiry,
            "vendor": a.vendor.name if a.vendor else None,
        }
        for a in assets
    ]
    return Response({"days": days, "count": len(data), "results": data})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def allocation_report(request):
    """Active allocations by department."""
    return Response(
        {
            "results": [
                {
                    "department": row["department"],
                    "department_code": row["department_code"],
                    "active_allocations": row["asset_count"],
                }
                for row in report_data.assets_by_department_summary()
            ]
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def request_pipeline_report(request):
    """Asset request counts by status."""
    rows = (
        AssetRequest.objects.values("status")
        .annotate(count=Count("id"))
        .order_by("status")
    )
    return Response({"results": list(rows), "total": AssetRequest.objects.count()})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def assets_by_department_json(request):
    return Response(
        {
            "summary": report_data.assets_by_department_summary(),
            "results": report_data.assets_by_department_rows(),
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def assets_by_category_json(request):
    return Response(
        {
            "summary": report_data.assets_by_category_summary(),
            "results": report_data.assets_by_category_rows(),
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def allocation_history_json(request):
    return Response({"results": report_data.allocation_history_rows()})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def maintenance_history_json(request):
    return Response({"results": report_data.maintenance_history_rows()})


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdminOrITTeam])
def inventory_csv(request):
    """CSV export of the full asset inventory."""
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "asset_tag",
            "name",
            "category",
            "status",
            "serial_number",
            "brand",
            "model",
            "vendor",
            "purchase_date",
            "purchase_cost",
            "warranty_expiry",
        ]
    )
    for asset in Asset.objects.select_related("category", "vendor").order_by("asset_tag"):
        writer.writerow(
            [
                asset.asset_tag,
                asset.name,
                asset.category.name,
                asset.status,
                asset.serial_number,
                asset.brand,
                asset.model,
                asset.vendor.name if asset.vendor else "",
                asset.purchase_date or "",
                asset.purchase_cost or "",
                asset.warranty_expiry or "",
            ]
        )
    response = HttpResponse(buffer.getvalue(), content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="asset_inventory.csv"'
    return response


# --- Excel exports (openpyxl) ---


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdminOrITTeam])
def assets_by_department_xlsx(request):
    return _file_response(
        export_assets_by_department_excel(),
        filename="assets_by_department.xlsx",
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdminOrITTeam])
def assets_by_category_xlsx(request):
    return _file_response(
        export_assets_by_category_excel(),
        filename="assets_by_category.xlsx",
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdminOrITTeam])
def allocation_history_xlsx(request):
    return _file_response(
        export_allocation_history_excel(),
        filename="allocation_history.xlsx",
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdminOrITTeam])
def maintenance_history_xlsx(request):
    return _file_response(
        export_maintenance_history_excel(),
        filename="maintenance_history.xlsx",
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


# --- PDF exports (ReportLab) ---


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdminOrITTeam])
def assets_by_department_pdf(request):
    return _file_response(
        export_assets_by_department_pdf(),
        filename="assets_by_department.pdf",
        content_type="application/pdf",
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdminOrITTeam])
def assets_by_category_pdf(request):
    return _file_response(
        export_assets_by_category_pdf(),
        filename="assets_by_category.pdf",
        content_type="application/pdf",
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdminOrITTeam])
def allocation_history_pdf(request):
    return _file_response(
        export_allocation_history_pdf(),
        filename="allocation_history.pdf",
        content_type="application/pdf",
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdminOrITTeam])
def maintenance_history_pdf(request):
    return _file_response(
        export_maintenance_history_pdf(),
        filename="maintenance_history.pdf",
        content_type="application/pdf",
    )
