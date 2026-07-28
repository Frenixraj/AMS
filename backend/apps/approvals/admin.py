from django.contrib import admin

from .models import Approval, AssetRequest


class ApprovalInline(admin.TabularInline):
    model = Approval
    extra = 0
    autocomplete_fields = ("approver",)


@admin.register(AssetRequest)
class AssetRequestAdmin(admin.ModelAdmin):
    list_display = (
        "request_number",
        "requested_by",
        "category",
        "asset",
        "priority",
        "status",
        "fulfilled_at",
        "created_at",
    )
    list_filter = ("status", "priority")
    search_fields = ("request_number", "requested_by__employee_code")
    autocomplete_fields = ("requested_by", "category", "asset", "fulfilled_by", "assignment")
    readonly_fields = ("fulfilled_at",)
    inlines = [ApprovalInline]


@admin.register(Approval)
class ApprovalAdmin(admin.ModelAdmin):
    list_display = (
        "asset_request",
        "step",
        "approver",
        "decision",
        "decided_at",
        "created_at",
    )
    list_filter = ("decision",)
    search_fields = ("asset_request__request_number", "approver__email")
    autocomplete_fields = ("asset_request", "approver")
