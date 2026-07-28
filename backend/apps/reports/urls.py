from django.urls import path

from reports import views

app_name = "reports"

urlpatterns = [
    path("health/", views.health_check, name="health"),
    # JSON summaries
    path("inventory/", views.inventory_summary, name="inventory"),
    path("warranty/", views.warranty_report, name="warranty"),
    path("allocations/", views.allocation_report, name="allocations"),
    path("requests/", views.request_pipeline_report, name="requests"),
    path("assets-by-department/", views.assets_by_department_json, name="assets-by-department"),
    path("assets-by-category/", views.assets_by_category_json, name="assets-by-category"),
    path("assets-by-person/", views.assets_by_person_json, name="assets-by-person"),
    path("allocation-history/", views.allocation_history_json, name="allocation-history"),
    path("maintenance-history/", views.maintenance_history_json, name="maintenance-history"),
    # Legacy CSV
    path("inventory.csv", views.inventory_csv, name="inventory-csv"),
    # Excel (openpyxl)
    path(
        "export/assets-by-department.xlsx",
        views.assets_by_department_xlsx,
        name="export-assets-by-department-xlsx",
    ),
    path(
        "export/assets-by-category.xlsx",
        views.assets_by_category_xlsx,
        name="export-assets-by-category-xlsx",
    ),
    path(
        "export/allocation-history.xlsx",
        views.allocation_history_xlsx,
        name="export-allocation-history-xlsx",
    ),
    path(
        "export/maintenance-history.xlsx",
        views.maintenance_history_xlsx,
        name="export-maintenance-history-xlsx",
    ),
    # PDF (ReportLab)
    path(
        "export/assets-by-department.pdf",
        views.assets_by_department_pdf,
        name="export-assets-by-department-pdf",
    ),
    path(
        "export/assets-by-category.pdf",
        views.assets_by_category_pdf,
        name="export-assets-by-category-pdf",
    ),
    path(
        "export/allocation-history.pdf",
        views.allocation_history_pdf,
        name="export-allocation-history-pdf",
    ),
    path(
        "export/maintenance-history.pdf",
        views.maintenance_history_pdf,
        name="export-maintenance-history-pdf",
    ),
]
