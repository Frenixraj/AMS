"""API views for Asset Management."""

from django.db import transaction
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from assets.filters import AssetCategoryFilter, AssetFilter, VendorFilter
from assets.models import Asset, AssetAssignment, AssetCategory, Vendor
from assets.serializers import (
    AssetCategorySerializer,
    AssetListSerializer,
    AssetSerializer,
    VendorSerializer,
)
from assets.services.assignment import (
    AssignAssetSerializer,
    AssetAssignmentSerializer,
    ReturnAssetSerializer,
    assign_asset,
    return_assignment,
)
from assets.services.audit import asset_snapshot, log_asset_change
from assets.services.qr import generate_asset_qr_code
from common.models import AuditLog
from common.permissions import IsAdminOrITTeam, IsAdminOrITTeamOrReadOnly
from notifications.models import Notification
from notifications.services import notify_admins_and_managers
from rest_framework.permissions import IsAuthenticated


class AssetCategoryViewSet(viewsets.ModelViewSet):
    """
    Supporting lookup CRUD for asset categories (within Asset module).
    Required so Asset forms can resolve category FKs.
    """

    queryset = AssetCategory.objects.all()
    serializer_class = AssetCategorySerializer
    permission_classes = [IsAdminOrITTeamOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = AssetCategoryFilter
    search_fields = ("name", "code", "description")
    ordering_fields = ("name", "code", "created_at")
    ordering = ("name",)

    def perform_create(self, serializer):
        category = serializer.save()
        notify_admins_and_managers(
            title="New category added",
            message=f"Category {category.code} ({category.name}) was created.",
            notification_type=Notification.NotificationType.INFO,
            link="/master-data",
            entity_type="assets.AssetCategory",
            entity_id=category.id,
            exclude_user_id=self.request.user.id,
        )


class VendorViewSet(viewsets.ModelViewSet):
    """Supporting lookup CRUD for vendors (within Asset module)."""

    queryset = Vendor.objects.all()
    serializer_class = VendorSerializer
    permission_classes = [IsAdminOrITTeamOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = VendorFilter
    search_fields = ("name", "email", "contact_person", "phone")
    ordering_fields = ("name", "created_at")
    ordering = ("name",)

    def perform_create(self, serializer):
        vendor = serializer.save()
        notify_admins_and_managers(
            title="New vendor added",
            message=f"Vendor {vendor.name} was created.",
            notification_type=Notification.NotificationType.INFO,
            link="/master-data",
            entity_type="assets.Vendor",
            entity_id=vendor.id,
            exclude_user_id=self.request.user.id,
        )


class AssetViewSet(viewsets.ModelViewSet):
    """
    Full Asset CRUD with image upload, QR generation, filter/search/order,
    pagination (global DRF settings), and audit logging.
    """

    queryset = (
        Asset.objects.select_related("category", "vendor", "created_by")
        .prefetch_related(
            Prefetch(
                "assignments",
                queryset=AssetAssignment.objects.filter(
                    status=AssetAssignment.Status.ACTIVE
                ).select_related("employee__user", "employee__department"),
                to_attr="_active_assignment_list",
            )
        )
        .all()
    )
    permission_classes = [IsAdminOrITTeamOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = AssetFilter
    search_fields = (
        "asset_tag",
        "name",
        "serial_number",
        "brand",
        "model",
        "notes",
    )
    ordering_fields = (
        "asset_tag",
        "name",
        "status",
        "purchase_date",
        "purchase_cost",
        "warranty_expiry",
        "created_at",
        "updated_at",
    )
    ordering = ("-created_at",)

    def get_serializer_class(self):
        if self.action == "list":
            return AssetListSerializer
        return AssetSerializer

    @transaction.atomic
    def perform_create(self, serializer):
        asset = serializer.save(created_by=self.request.user)
        generate_asset_qr_code(asset)
        log_asset_change(
            actor=self.request.user,
            action=AuditLog.Action.CREATE,
            asset=asset,
            after=asset_snapshot(asset),
            request=self.request,
        )
        notify_admins_and_managers(
            title="New asset added",
            message=f"{asset.asset_tag} ({asset.name}) was added to inventory.",
            notification_type=Notification.NotificationType.INFO,
            link=f"/assets/{asset.id}",
            entity_type="assets.Asset",
            entity_id=asset.id,
            exclude_user_id=self.request.user.id,
        )

    @transaction.atomic
    def perform_update(self, serializer):
        before = asset_snapshot(serializer.instance)
        previous_tag = serializer.instance.asset_tag
        asset = serializer.save()
        # Regenerate QR when the business tag changes so payload stays accurate.
        if asset.asset_tag != previous_tag or not asset.qr_code:
            generate_asset_qr_code(asset)
        after = asset_snapshot(asset)
        action = (
            AuditLog.Action.STATUS_CHANGE
            if before.get("status") != after.get("status")
            else AuditLog.Action.UPDATE
        )
        log_asset_change(
            actor=self.request.user,
            action=action,
            asset=asset,
            before=before,
            after=after,
            request=self.request,
        )

    @transaction.atomic
    def perform_destroy(self, instance):
        before = asset_snapshot(instance)
        asset_id = instance.pk
        log_asset_change(
            actor=self.request.user,
            action=AuditLog.Action.DELETE,
            asset=instance,
            before=before,
            request=self.request,
        )
        # AuditLog stores entity_id as string; delete after logging.
        instance.delete()
        # Re-write entity_id is already set from pk before delete — fine.
        _ = asset_id

    @action(detail=False, methods=["get"], url_path="by-tag/(?P<asset_tag>[^/.]+)")
    def by_tag(self, request, asset_tag=None):
        """
        Resolve a scanned QR payload's asset tag to a full asset detail.
        Used by the SPA camera scanner after decoding ASSETFLOW:{tag}.
        """
        asset = get_object_or_404(
            self.get_queryset(),
            asset_tag__iexact=asset_tag,
        )
        serializer = AssetSerializer(asset, context={"request": request})
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="regenerate-qr")
    def regenerate_qr(self, request, pk=None):
        """Force regenerate the QR image for an asset."""
        asset = self.get_object()
        generate_asset_qr_code(asset)
        log_asset_change(
            actor=request.user,
            action=AuditLog.Action.UPDATE,
            asset=asset,
            after={"qr_code": "regenerated", **asset_snapshot(asset)},
            request=request,
        )
        serializer = AssetSerializer(asset, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"], url_path="audit-logs")
    def audit_logs(self, request, pk=None):
        """Return audit history for this asset."""
        asset = self.get_object()
        logs = (
            AuditLog.objects.filter(
                entity_type="assets.Asset",
                entity_id=str(asset.pk),
            )
            .select_related("actor")
            .order_by("-created_at")[:50]
        )
        data = [
            {
                "id": log.id,
                "action": log.action,
                "actor_email": log.actor.email if log.actor else None,
                "changes": log.changes,
                "ip_address": log.ip_address,
                "created_at": log.created_at,
            }
            for log in logs
        ]
        return Response(data)


class AssetAssignmentViewSet(viewsets.ReadOnlyModelViewSet):
    """List/retrieve assignments; assign and return via custom actions."""

    queryset = AssetAssignment.objects.select_related(
        "asset",
        "employee",
        "employee__user",
        "assigned_by",
    ).all()
    serializer_class = AssetAssignmentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ("status", "asset", "employee")
    search_fields = ("asset__asset_tag", "employee__employee_code", "employee__user__email")
    ordering_fields = ("assigned_at", "returned_at", "created_at")
    ordering = ("-assigned_at",)

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.role == "EMPLOYEE" and hasattr(user, "employee_profile"):
            return qs.filter(employee=user.employee_profile)
        if user.role == "MANAGER":
            return qs.filter(employee__department__manager=user)
        return qs

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated, IsAdminOrITTeam])
    def assign(self, request):
        serializer = AssignAssetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        assignment = assign_asset(
            asset_id=serializer.validated_data["asset_id"],
            employee_id=serializer.validated_data["employee_id"],
            actor=request.user,
            notes=serializer.validated_data.get("notes", ""),
            request=request,
        )
        return Response(
            AssetAssignmentSerializer(assignment).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated, IsAdminOrITTeam])
    def return_asset(self, request, pk=None):
        assignment = self.get_object()
        serializer = ReturnAssetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        updated = return_assignment(
            assignment=assignment,
            actor=request.user,
            notes=serializer.validated_data.get("notes", ""),
            request=request,
        )
        return Response(AssetAssignmentSerializer(updated).data)
