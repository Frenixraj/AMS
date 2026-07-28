import django_filters

from employees.models import Department, Employee


class DepartmentFilter(django_filters.FilterSet):
    is_active = django_filters.BooleanFilter()
    code = django_filters.CharFilter(lookup_expr="iexact")

    class Meta:
        model = Department
        fields = ("is_active", "code", "manager")


class EmployeeFilter(django_filters.FilterSet):
    is_active = django_filters.BooleanFilter()
    department = django_filters.NumberFilter(field_name="department_id")
    employee_code = django_filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = Employee
        fields = ("is_active", "department", "employee_code")
