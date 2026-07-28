from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ("email", "username", "role", "is_active", "is_staff", "date_joined")
    list_filter = ("role", "is_active", "is_staff")
    search_fields = ("email", "username", "first_name", "last_name")
    ordering = ("email",)

    fieldsets = DjangoUserAdmin.fieldsets + (
        ("AssetFlow", {"fields": ("role",)}),
    )
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        ("AssetFlow", {"fields": ("email", "role")}),
    )
