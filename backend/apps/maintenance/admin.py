from django.contrib import admin

from .models import MaintenanceRecord


@admin.register(MaintenanceRecord)
class MaintenanceRecordAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "asset",
        "status",
        "reported_by",
        "assigned_to",
        "created_at",
    )
    list_filter = ("status",)
    search_fields = ("title", "asset__asset_tag", "reported_by__employee_code")
    autocomplete_fields = ("asset", "reported_by", "assigned_to")
