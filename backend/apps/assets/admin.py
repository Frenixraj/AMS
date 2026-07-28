from django.contrib import admin

from .models import Asset, AssetAssignment, AssetCategory, Vendor


@admin.register(AssetCategory)
class AssetCategoryAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("code", "name")


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "phone", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "email", "contact_person")


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = (
        "asset_tag",
        "name",
        "category",
        "serial_number",
        "status",
        "vendor",
        "created_at",
    )
    list_filter = ("status", "category", "vendor")
    search_fields = ("asset_tag", "name", "serial_number", "brand", "model")
    autocomplete_fields = ("category", "vendor", "created_by")
    readonly_fields = ("created_at", "updated_at")


@admin.register(AssetAssignment)
class AssetAssignmentAdmin(admin.ModelAdmin):
    list_display = (
        "asset",
        "employee",
        "status",
        "assigned_at",
        "returned_at",
        "assigned_by",
    )
    list_filter = ("status",)
    search_fields = ("asset__asset_tag", "employee__employee_code")
    autocomplete_fields = ("asset", "employee", "assigned_by")
