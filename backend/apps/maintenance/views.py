"""Maintenance ticket API."""

from __future__ import annotations

from django.db import transaction
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from assets.models import Asset
from common.models import AuditLog
from common.permissions import IsAdminOrITTeamOrReadOnly
from common.utils import write_audit_log
from maintenance.models import MaintenanceRecord


class MaintenanceRecordSerializer(serializers.ModelSerializer):
    asset_tag = serializers.CharField(source="asset.asset_tag", read_only=True)
    reported_by_code = serializers.CharField(
        source="reported_by.employee_code",
        read_only=True,
    )
    assigned_to_email = serializers.EmailField(
        source="assigned_to.email",
        read_only=True,
        default=None,
    )

    class Meta:
        model = MaintenanceRecord
        fields = (
            "id",
            "asset",
            "asset_tag",
            "reported_by",
            "reported_by_code",
            "assigned_to",
            "assigned_to_email",
            "title",
            "issue_description",
            "status",
            "cost",
            "started_at",
            "completed_at",
            "resolution_notes",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "reported_by", "created_at", "updated_at")


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    return Response({"status": "ok", "app": "maintenance"})


class MaintenanceRecordViewSet(viewsets.ModelViewSet):
    queryset = MaintenanceRecord.objects.select_related(
        "asset",
        "reported_by",
        "reported_by__user",
        "assigned_to",
    ).all()
    serializer_class = MaintenanceRecordSerializer
    permission_classes = [IsAuthenticated, IsAdminOrITTeamOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ("status", "asset", "assigned_to", "reported_by")
    search_fields = ("title", "issue_description", "asset__asset_tag")
    ordering_fields = ("created_at", "status", "completed_at")
    ordering = ("-created_at",)

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.role == "EMPLOYEE" and hasattr(user, "employee_profile"):
            return qs.filter(reported_by=user.employee_profile)
        if user.role == "MANAGER":
            return qs.filter(reported_by__department__manager=user)
        return qs

    def get_permissions(self):
        # Employees may create (report issue) and list their tickets.
        if self.action == "create":
            return [IsAuthenticated()]
        return super().get_permissions()

    @transaction.atomic
    def perform_create(self, serializer):
        user = self.request.user
        if not hasattr(user, "employee_profile"):
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("Employee profile required to report issues.")
        record = serializer.save(reported_by=user.employee_profile)
        asset = Asset.objects.select_for_update().get(pk=record.asset_id)
        if asset.status in (Asset.Status.AVAILABLE, Asset.Status.ALLOCATED):
            asset.status = Asset.Status.MAINTENANCE
            asset.save(update_fields=["status", "updated_at"])
        write_audit_log(
            actor=user,
            action=AuditLog.Action.CREATE,
            entity_type="maintenance.MaintenanceRecord",
            entity_id=record.pk,
            changes={"asset_id": record.asset_id, "status": record.status},
            request=self.request,
        )

    @transaction.atomic
    def perform_update(self, serializer):
        previous = serializer.instance.status
        record = serializer.save()
        if (
            previous != MaintenanceRecord.Status.COMPLETED
            and record.status == MaintenanceRecord.Status.COMPLETED
        ):
            if not record.completed_at:
                record.completed_at = timezone.now()
                record.save(update_fields=["completed_at", "updated_at"])
            asset = Asset.objects.select_for_update().get(pk=record.asset_id)
            if asset.status == Asset.Status.MAINTENANCE:
                # Restore to allocated if still assigned, else available.
                has_active = asset.assignments.filter(status="ACTIVE").exists()
                asset.status = (
                    Asset.Status.ALLOCATED if has_active else Asset.Status.AVAILABLE
                )
                asset.save(update_fields=["status", "updated_at"])
        write_audit_log(
            actor=self.request.user,
            action=AuditLog.Action.UPDATE,
            entity_type="maintenance.MaintenanceRecord",
            entity_id=record.pk,
            changes={"status": record.status},
            request=self.request,
        )

    @action(detail=True, methods=["post"])
    def start(self, request, pk=None):
        record = self.get_object()
        record.status = MaintenanceRecord.Status.IN_PROGRESS
        record.started_at = timezone.now()
        if not record.assigned_to_id:
            record.assigned_to = request.user
        record.save(update_fields=["status", "started_at", "assigned_to", "updated_at"])
        return Response(MaintenanceRecordSerializer(record).data)

    @action(detail=True, methods=["post"])
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
            asset.status = Asset.Status.ALLOCATED if has_active else Asset.Status.AVAILABLE
            asset.save(update_fields=["status", "updated_at"])
        return Response(MaintenanceRecordSerializer(record).data)
