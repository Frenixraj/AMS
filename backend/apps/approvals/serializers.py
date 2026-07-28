"""Serializers for asset request / approval workflow."""

from __future__ import annotations

from rest_framework import serializers

from approvals.models import Approval, AssetRequest
from approvals.services.workflow import build_timeline
from assets.models import Asset


class ApprovalSerializer(serializers.ModelSerializer):
    approver_email = serializers.EmailField(source="approver.email", read_only=True, default=None)

    class Meta:
        model = Approval
        fields = (
            "id",
            "step",
            "approver",
            "approver_email",
            "decision",
            "comments",
            "decided_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class AssetRequestListSerializer(serializers.ModelSerializer):
    requested_by_code = serializers.CharField(
        source="requested_by.employee_code",
        read_only=True,
    )
    requested_by_email = serializers.EmailField(
        source="requested_by.user.email",
        read_only=True,
    )
    department_name = serializers.CharField(
        source="requested_by.department.name",
        read_only=True,
    )
    category_name = serializers.CharField(source="category.name", read_only=True, default=None)
    asset_tag = serializers.CharField(source="asset.asset_tag", read_only=True, default=None)

    class Meta:
        model = AssetRequest
        fields = (
            "id",
            "request_number",
            "requested_by",
            "requested_by_code",
            "requested_by_email",
            "department_name",
            "category",
            "category_name",
            "asset",
            "asset_tag",
            "priority",
            "status",
            "created_at",
            "updated_at",
            "fulfilled_at",
        )


class AssetRequestSerializer(serializers.ModelSerializer):
    requested_by_code = serializers.CharField(
        source="requested_by.employee_code",
        read_only=True,
    )
    requested_by_email = serializers.EmailField(
        source="requested_by.user.email",
        read_only=True,
    )
    department_name = serializers.CharField(
        source="requested_by.department.name",
        read_only=True,
    )
    category_name = serializers.CharField(source="category.name", read_only=True, default=None)
    asset_tag = serializers.CharField(source="asset.asset_tag", read_only=True, default=None)
    asset_name = serializers.CharField(source="asset.name", read_only=True, default=None)
    fulfilled_by_email = serializers.EmailField(
        source="fulfilled_by.email",
        read_only=True,
        default=None,
    )
    approvals = ApprovalSerializer(many=True, read_only=True)
    timeline = serializers.SerializerMethodField()

    class Meta:
        model = AssetRequest
        fields = (
            "id",
            "request_number",
            "requested_by",
            "requested_by_code",
            "requested_by_email",
            "department_name",
            "category",
            "category_name",
            "asset",
            "asset_tag",
            "asset_name",
            "justification",
            "priority",
            "status",
            "fulfilled_at",
            "fulfilled_by",
            "fulfilled_by_email",
            "assignment",
            "approvals",
            "timeline",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "request_number",
            "requested_by",
            "status",
            "fulfilled_at",
            "fulfilled_by",
            "assignment",
            "created_at",
            "updated_at",
        )

    def get_timeline(self, obj: AssetRequest):
        return build_timeline(obj)


class AssetRequestCreateSerializer(serializers.Serializer):
    category = serializers.IntegerField(required=False, allow_null=True)
    asset = serializers.IntegerField(required=False, allow_null=True)
    justification = serializers.CharField(min_length=10, max_length=4000)
    priority = serializers.ChoiceField(
        choices=AssetRequest.Priority.choices,
        default=AssetRequest.Priority.MEDIUM,
    )

    def validate(self, attrs):
        if not attrs.get("category") and not attrs.get("asset"):
            raise serializers.ValidationError(
                "Provide a category and/or a specific asset."
            )
        asset_id = attrs.get("asset")
        if asset_id:
            if not Asset.objects.filter(pk=asset_id).exists():
                raise serializers.ValidationError({"asset": "Asset not found."})
        return attrs


class DecisionSerializer(serializers.Serializer):
    comments = serializers.CharField(required=False, allow_blank=True, default="", max_length=2000)


class FulfillSerializer(serializers.Serializer):
    asset_id = serializers.IntegerField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True, default="", max_length=2000)
