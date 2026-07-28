"""Serializers for the Asset Management module."""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from rest_framework import serializers

from assets.models import Asset, AssetAssignment, AssetCategory, Vendor


def absolute_media_url(request, field) -> Optional[str]:
    if not field:
        return None
    url = field.url
    if request is not None:
        return request.build_absolute_uri(url)
    return url


def _current_owner_payload(obj: Asset) -> Optional[dict]:
    assignment = None
    active_list = getattr(obj, "_active_assignment_list", None)
    if active_list:
        assignment = active_list[0]
    elif assignment is None:
        assignment = (
            AssetAssignment.objects.filter(
                asset_id=obj.pk,
                status=AssetAssignment.Status.ACTIVE,
            )
            .select_related("employee__user", "employee__department")
            .first()
        )
    if assignment is None:
        return None
    emp = assignment.employee
    user = emp.user
    full_name = f"{user.first_name} {user.last_name}".strip() or user.email
    return {
        "assignment_id": assignment.id,
        "employee_id": emp.id,
        "employee_code": emp.employee_code,
        "full_name": full_name,
        "email": user.email,
        "phone": emp.phone,
        "job_title": emp.job_title,
        "department_id": emp.department_id,
        "department_name": emp.department.name,
        "assigned_at": assignment.assigned_at.isoformat(),
    }


class AssetCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = AssetCategory
        fields = (
            "id",
            "name",
            "code",
            "description",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class VendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = (
            "id",
            "name",
            "contact_person",
            "email",
            "phone",
            "address",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class AssetListSerializer(serializers.ModelSerializer):
    """Lean serializer for paginated inventory tables."""

    category_name = serializers.CharField(source="category.name", read_only=True)
    vendor_name = serializers.CharField(source="vendor.name", read_only=True, default=None)
    image_url = serializers.SerializerMethodField()
    qr_code_url = serializers.SerializerMethodField()
    current_owner = serializers.SerializerMethodField()

    class Meta:
        model = Asset
        fields = (
            "id",
            "asset_tag",
            "name",
            "category",
            "category_name",
            "brand",
            "model",
            "serial_number",
            "status",
            "vendor",
            "vendor_name",
            "purchase_date",
            "purchase_cost",
            "warranty_expiry",
            "image_url",
            "qr_code_url",
            "current_owner",
            "created_at",
            "updated_at",
        )

    def get_image_url(self, obj: Asset) -> Optional[str]:
        return absolute_media_url(self.context.get("request"), obj.image)

    def get_qr_code_url(self, obj: Asset) -> Optional[str]:
        return absolute_media_url(self.context.get("request"), obj.qr_code)

    def get_current_owner(self, obj: Asset) -> Optional[dict]:
        return _current_owner_payload(obj)


class AssetSerializer(serializers.ModelSerializer):
    """Full create / update / detail serializer with nested labels and media URLs."""

    category_detail = AssetCategorySerializer(source="category", read_only=True)
    vendor_detail = VendorSerializer(source="vendor", read_only=True)
    created_by_email = serializers.EmailField(
        source="created_by.email",
        read_only=True,
        default=None,
    )
    image_url = serializers.SerializerMethodField()
    qr_code_url = serializers.SerializerMethodField()
    qr_payload = serializers.SerializerMethodField()
    current_owner = serializers.SerializerMethodField()

    class Meta:
        model = Asset
        fields = (
            "id",
            "asset_tag",
            "name",
            "category",
            "category_detail",
            "brand",
            "model",
            "serial_number",
            "purchase_date",
            "purchase_cost",
            "vendor",
            "vendor_detail",
            "warranty_expiry",
            "status",
            "image",
            "image_url",
            "qr_code",
            "qr_code_url",
            "qr_payload",
            "current_owner",
            "notes",
            "created_by",
            "created_by_email",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "qr_code",
            "created_by",
            "created_at",
            "updated_at",
            "current_owner",
        )
        extra_kwargs = {
            "image": {"write_only": True, "required": False},
        }

    def get_image_url(self, obj: Asset) -> Optional[str]:
        return absolute_media_url(self.context.get("request"), obj.image)

    def get_qr_code_url(self, obj: Asset) -> Optional[str]:
        return absolute_media_url(self.context.get("request"), obj.qr_code)

    def get_qr_payload(self, obj: Asset) -> str:
        from assets.services.qr import build_qr_payload

        return build_qr_payload(obj)

    def get_current_owner(self, obj: Asset) -> Optional[dict]:
        return _current_owner_payload(obj)

    def validate_asset_tag(self, value: str) -> str:
        value = value.strip().upper()
        if not value:
            raise serializers.ValidationError("Asset tag is required.")
        qs = Asset.objects.filter(asset_tag__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("An asset with this tag already exists.")
        return value

    def validate_serial_number(self, value: str) -> str:
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Serial number is required.")
        qs = Asset.objects.filter(serial_number__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(
                "An asset with this serial number already exists."
            )
        return value

    def validate_purchase_cost(self, value: Optional[Decimal]) -> Optional[Decimal]:
        if value is not None and value < 0:
            raise serializers.ValidationError("Purchase cost cannot be negative.")
        return value

    def validate(self, attrs: dict) -> dict:
        purchase_date = attrs.get(
            "purchase_date",
            getattr(self.instance, "purchase_date", None),
        )
        warranty_expiry = attrs.get(
            "warranty_expiry",
            getattr(self.instance, "warranty_expiry", None),
        )
        if purchase_date and warranty_expiry and warranty_expiry < purchase_date:
            raise serializers.ValidationError(
                {"warranty_expiry": "Warranty expiry cannot be before purchase date."}
            )
        return attrs

    def validate_status(self, value: str) -> str:
        from assets.services.status import assert_transition

        valid = {choice.value for choice in Asset.Status}
        if value not in valid:
            raise serializers.ValidationError(
                f"Invalid status. Choose from: {', '.join(sorted(valid))}."
            )
        if self.instance is not None:
            try:
                assert_transition(self.instance.status, value)
            except ValueError as exc:
                raise serializers.ValidationError(str(exc)) from exc
        return value
