"""PDF (ReportLab) report exporters."""

from __future__ import annotations

import io
from typing import Any, Sequence

from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from reports.services import data as report_data


def _pdf_bytes(
    *,
    title: str,
    headers: Sequence[str],
    rows: list[dict[str, Any]],
    keys: Sequence[str],
    landscape_mode: bool = True,
) -> bytes:
    buffer = io.BytesIO()
    page = landscape(A4) if landscape_mode else A4
    doc = SimpleDocTemplate(
        buffer,
        pagesize=page,
        leftMargin=12 * mm,
        rightMargin=12 * mm,
        topMargin=14 * mm,
        bottomMargin=14 * mm,
        title=title,
    )
    styles = getSampleStyleSheet()
    story = [
        Paragraph(f"<b>AssetFlow — {title}</b>", styles["Title"]),
        Paragraph(
            f"Generated {timezone.now().strftime('%Y-%m-%d %H:%M UTC')}",
            styles["Normal"],
        ),
        Spacer(1, 8),
    ]

    table_data = [list(headers)]
    for row in rows:
        table_data.append([str(row.get(key, "") or "") for key in keys])

    if len(table_data) == 1:
        table_data.append(["—"] * len(headers))

    table = Table(table_data, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F2937")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    story.append(table)
    doc.build(story)
    return buffer.getvalue()


def export_assets_by_department_pdf() -> bytes:
    return _pdf_bytes(
        title="Assets by Department",
        headers=[
            "Department",
            "Code",
            "Asset Tag",
            "Asset Name",
            "Category",
            "Employee",
            "Assigned At",
        ],
        rows=report_data.assets_by_department_rows(),
        keys=[
            "department",
            "department_code",
            "asset_tag",
            "asset_name",
            "category",
            "employee_code",
            "assigned_at",
        ],
    )


def export_assets_by_category_pdf() -> bytes:
    return _pdf_bytes(
        title="Assets by Category",
        headers=[
            "Category",
            "Asset Tag",
            "Asset Name",
            "Status",
            "Serial",
            "Brand",
            "Vendor",
        ],
        rows=report_data.assets_by_category_rows(),
        keys=[
            "category",
            "asset_tag",
            "asset_name",
            "status",
            "serial_number",
            "brand",
            "vendor",
        ],
    )


def export_allocation_history_pdf() -> bytes:
    return _pdf_bytes(
        title="Allocation History",
        headers=[
            "Asset Tag",
            "Employee",
            "Department",
            "Status",
            "Assigned At",
            "Returned At",
            "Assigned By",
        ],
        rows=report_data.allocation_history_rows(),
        keys=[
            "asset_tag",
            "employee_code",
            "department",
            "status",
            "assigned_at",
            "returned_at",
            "assigned_by",
        ],
    )


def export_maintenance_history_pdf() -> bytes:
    return _pdf_bytes(
        title="Maintenance History",
        headers=[
            "Asset Tag",
            "Title",
            "Status",
            "Reported By",
            "Assigned To",
            "Created At",
            "Completed At",
        ],
        rows=report_data.maintenance_history_rows(),
        keys=[
            "asset_tag",
            "title",
            "status",
            "reported_by",
            "assigned_to",
            "created_at",
            "completed_at",
        ],
    )
