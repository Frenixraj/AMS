from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("action", "entity_type", "entity_id", "actor", "created_at")
    list_filter = ("action", "entity_type")
    search_fields = ("entity_type", "entity_id", "actor__email")
    autocomplete_fields = ("actor",)
    readonly_fields = (
        "actor",
        "action",
        "entity_type",
        "entity_id",
        "changes",
        "ip_address",
        "user_agent",
        "created_at",
        "updated_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
