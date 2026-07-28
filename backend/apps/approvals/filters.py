"""FilterSet for asset requests."""

import django_filters

from approvals.models import AssetRequest


class AssetRequestFilter(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(choices=AssetRequest.Status.choices)
    priority = django_filters.ChoiceFilter(choices=AssetRequest.Priority.choices)
    category = django_filters.NumberFilter(field_name="category_id")
    requested_by = django_filters.NumberFilter(field_name="requested_by_id")
    department = django_filters.NumberFilter(field_name="requested_by__department_id")

    class Meta:
        model = AssetRequest
        fields = ("status", "priority", "category", "requested_by", "department")
