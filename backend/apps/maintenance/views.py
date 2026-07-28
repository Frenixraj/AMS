"""Maintenance ticket API with manager/admin approval."""

from __future__ import annotations

from django.db import transaction
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from assets.models import Asset, AssetAssignment
from common.models import AuditLog
from common.permissions import IsAdminOrAssetManagerOrReadOnly, _role
from common.utils import write_audit_log
from maintenance.models import MaintenanceRecord
from notifications.models import Notification
from notifications.services import notify_admin_mailbox, notify_admins_and_managers, notify_user


class MaintenanceRecordSerializer(serializers.ModelSerializer):
    asset_tag = serializers.CharField(source="asset.asset_tag", read_only=True)
    asset_name = serializers.CharField(source="asset.name", read_only=True)
    reported_by_code = serializers.CharField(
        source="reported_by.employee_code",
        read_only=True,
    )
    reported_by_name = serializers.SerializerMethodField()
    assigned_to_email = serializers.EmailField(
        source="assigned_to.email",
        read_only=True,
        default=None,
    )
    decided_by_email = serializers.EmailField(
        source="decided_by.email",
        read_only=True,
        default=None,
    )

    class Meta:
        model = MaintenanceRecord
        fields = (
            "id",
            "asset",
            "asset_tag",
            "asset_name",
            "reported_by",
            "reported_by_code",
            "reported_by_name",
            "assigned_to",
            "assigned_to_email",
            "title",
            "issue_description",
            "status",
            "approval_comments",
            "decided_by",
            "decided_by_email",
            "decided_at",
            "cost",
            "started_at",
            "completed_at",
            "resolution_notes",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "reported_by",
            "status",
            "approval_comments",
            "decided_by",
            "decided_at",
            "created_at",
            "updated_at",
        )

    def get_reported_by_name(self, obj) -> str:
        u = obj.reported_by.user
        name = f"{u.first_name} {u.last_name}".strip()
        return name or u.email


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    return Response({"status": "ok", "app": "maintenance"})


def _can_approve_maintenance(user, record: MaintenanceRecord) -> bool:
    role = _role(user)
    if role == "ADMIN" or user.is_superuser:
        return True
    if role == "MANAGER":
        return record.reported_by.department.manager_id == user.id
    return False


class MaintenanceRecordViewSet(viewsets.ModelViewSet):
    queryset = MaintenanceRecord.objects.select_related(
        "asset",
        "reported_by",
        "reported_by__user",
        "reported_by__department",
        "assigned_to",
        "decided_by",
    ).all()
    serializer_class = MaintenanceRecordSerializer
    permission_classes = [IsAuthenticated, IsAdminOrAssetManagerOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ("status", "asset", "assigned_to", "reported_by")
    search_fields = ("title", "issue_description", "asset__asset_tag")
    ordering_fields = ("created_at", "status", "completed_at")
    ordering = ("-created_at",)

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        role = _role(user)
        if role == "EMPLOYEE" and hasattr(user, "employee_profile"):
            return qs.filter(reported_by=user.employee_profile)
        if role == "MANAGER":
            return qs.filter(reported_by__department__manager=user)
        return qs

    def get_permissions(self):
        if self.action in ("create", "list", "retrieve", "approve", "reject"):
            return [IsAuthenticated()]
        return super().get_permissions()

    @transaction.atomic
    def perform_create(self, serializer):
        user = self.request.user
        if not hasattr(user, "employee_profile"):
            raise PermissionDenied("Employee profile required to raise maintenance.")

        asset = Asset.objects.get(pk=serializer.validated_data["asset"].id)
        # Employee/manager may only service assets they currently own (or dept for manager)
        role = _role(user)
        owned = AssetAssignment.objects.filter(
            asset=asset,
            status=AssetAssignment.Status.ACTIVE,
        ).select_related("employee")
        if role == "EMPLOYEE":
            if not owned.filter(employee=user.employee_profile).exists():
                raise PermissionDenied("You can only service assets assigned to you.")
        elif role == "MANAGER":
            if not owned.filter(employee__department__manager=user).exists():
                raise PermissionDenied("You can only service assets in your department.")

        record = serializer.save(
            reported_by=user.employee_profile,
            status=MaintenanceRecord.Status.PENDING_APPROVAL,
        )
        # Do NOT flip asset to MAINTENANCE until approved

        write_audit_log(
            actor=user,
            action=AuditLog.Action.CREATE,
            entity_type="maintenance.MaintenanceRecord",
            entity_id=record.pk,
            changes={"asset_id": record.asset_id, "status": record.status},
            request=self.request,
        )

        notify_admins_and_managers(
            title=f"Maintenance request: {asset.asset_tag}",
            message=f"{user.email} requested service for {asset.asset_tag}: {record.title}",
            notification_type=Notification.NotificationType.MAINTENANCE,
            link="/maintenance",
            entity_type="maintenance.MaintenanceRecord",
            entity_id=record.pk,
            exclude_user_id=user.id,
        )
        notify_admin_mailbox(
            subject=f"[AssetFlow] Maintenance pending: {asset.asset_tag}",
            body=f"{user.email} raised maintenance for {asset.asset_tag}: {record.title}",
        )

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def approve(self, request, pk=None):
        record = self.get_object()
        if record.status != MaintenanceRecord.Status.PENDING_APPROVAL:
            raise ValidationError({"detail": "Only pending tickets can be approved."})
        if not _can_approve_maintenance(request.user, record):
            raise PermissionDenied("Only the department manager or admin can approve.")

        comments = request.data.get("comments", "")
        record.status = MaintenanceRecord.Status.OPEN
        record.approval_comments = comments or ""
        record.decided_by = request.user
        record.decided_at = timezone.now()
        record.save(
            update_fields=[
                "status",
                "approval_comments",
                "decided_by",
                "decided_at",
                "updated_at",
            ]
        )

        asset = Asset.objects.select_for_update().get(pk=record.asset_id)
        if asset.status in (Asset.Status.AVAILABLE, Asset.Status.ALLOCATED):
            asset.status = Asset.Status.MAINTENANCE
            asset.save(update_fields=["status", "updated_at"])

        notify_user(
            recipient=record.reported_by.user,
            title=f"Maintenance approved: {asset.asset_tag}",
            message="Your maintenance request was approved.",
            notification_type=Notification.NotificationType.MAINTENANCE,
            link="/maintenance",
            entity_type="maintenance.MaintenanceRecord",
            entity_id=record.pk,
        )
        notify_admin_mailbox(
            subject=f"[AssetFlow] Maintenance approved: {asset.asset_tag}",
            body=f"{request.user.email} approved maintenance for {asset.asset_tag}.",
        )
        return Response(MaintenanceRecordSerializer(record).data)

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def reject(self, request, pk=None):
        record = self.get_object()
        if record.status != MaintenanceRecord.Status.PENDING_APPROVAL:
            raise ValidationError({"detail": "Only pending tickets can be rejected."})
        if not _can_approve_maintenance(request.user, record):
            raise PermissionDenied("Only the department manager or admin can reject.")

        comments = request.data.get("comments", "")
        record.status = MaintenanceRecord.Status.REJECTED
        record.approval_comments = comments or ""
        record.decided_by = request.user
        record.decided_at = timezone.now()
        record.save(
            update_fields=[
                "status",
                "approval_comments",
                "decided_by",
                "decided_at",
                "updated_at",
            ]
        )
        notify_user(
            recipient=record.reported_by.user,
            title=f"Maintenance rejected: {record.asset.asset_tag}",
            message=comments or "Your maintenance request was rejected.",
            notification_type=Notification.NotificationType.MAINTENANCE,
            link="/maintenance",
            entity_type="maintenance.MaintenanceRecord",
            entity_id=record.pk,
        )
        return Response(MaintenanceRecordSerializer(record).data)

    @action(detail=True, methods=["post"])
    def start(self, request, pk=None):
        record = self.get_object()
        if record.status not in (
            MaintenanceRecord.Status.OPEN,
            MaintenanceRecord.Status.IN_PROGRESS,
        ):
            raise ValidationError({"detail": "Ticket must be approved (OPEN) first."})
        record.status = MaintenanceRecord.Status.IN_PROGRESS
        record.started_at = timezone.now()
        if not record.assigned_to_id:
            record.assigned_to = request.user
        record.save(update_fields=["status", "started_at", "assigned_to", "updated_at"])
        return Response(MaintenanceRecordSerializer(record).data)

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def complete(self, request, pk=None):
        record = self.get_object()
        notes = request.data.get("resolution_notes", "")
        record.status = MaintenanceRecord.Status.COMPLETED
        record.completed_at = timezone.now()
        if not record.started_at:
            record.started_at = record.completed_at
        if notes:
            record.resolution_notes = notes
        record.save(
            update_fields=[
                "status",
                "completed_at",
                "started_at",
                "resolution_notes",
                "updated_at",
            ]
        )
        asset = Asset.objects.select_for_update().get(pk=record.asset_id)
        if asset.status == Asset.Status.MAINTENANCE:
            has_active = asset.assignments.filter(status="ACTIVE").exists()
            asset.status = (
                Asset.Status.ALLOCATED if has_active else Asset.Status.AVAILABLE
            )
            asset.save(update_fields=["status", "updated_at"])
        return Response(MaintenanceRecordSerializer(record).data)
