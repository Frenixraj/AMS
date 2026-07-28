"""FilterSet definitions for Asset Management APIs."""

import django_filters

from assets.models import Asset, AssetCategory, Vendor


class AssetFilter(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(choices=Asset.Status.choices)
    category = django_filters.NumberFilter(field_name="category_id")
    vendor = django_filters.NumberFilter(field_name="vendor_id")
    brand = django_filters.CharFilter(lookup_expr="icontains")
    purchase_date_from = django_filters.DateFilter(
        field_name="purchase_date",
        lookup_expr="gte",
    )
    purchase_date_to = django_filters.DateFilter(
        field_name="purchase_date",
        lookup_expr="lte",
    )
    warranty_expiring_before = django_filters.DateFilter(
        field_name="warranty_expiry",
        lookup_expr="lte",
    )
    created_by = django_filters.NumberFilter(field_name="created_by_id")

    class Meta:
        model = Asset
        fields = (
            "status",
            "category",
            "vendor",
            "brand",
            "created_by",
        )


class AssetCategoryFilter(django_filters.FilterSet):
    is_active = django_filters.BooleanFilter()
    code = django_filters.CharFilter(lookup_expr="iexact")

    class Meta:
        model = AssetCategory
        fields = ("is_active", "code")


class VendorFilter(django_filters.FilterSet):
    is_active = django_filters.BooleanFilter()
    name = django_filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = Vendor
        fields = ("is_active", "name")
