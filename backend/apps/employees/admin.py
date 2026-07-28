from django.contrib import admin

from .models import Department, Employee


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "manager", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("code", "name")
    autocomplete_fields = ("manager",)


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = (
        "employee_code",
        "user",
        "department",
        "job_title",
        "is_active",
        "created_at",
    )
    list_filter = ("is_active", "department")
    search_fields = ("employee_code", "user__email", "user__username")
    autocomplete_fields = ("user", "department")
