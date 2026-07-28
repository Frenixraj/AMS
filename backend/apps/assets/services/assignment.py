"""Asset assignment serializers and assignment lifecycle API helpers."""

from __future__ import annotations

from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from assets.models import Asset, AssetAssignment
from common.models import AuditLog
from common.utils import write_audit_log
from employees.models import Employee
from notifications.models import Notification
from notifications.services import notify_admin_mailbox, notify_admins_and_managers, notify_user


class AssetAssignmentSerializer(serializers.ModelSerializer):
    asset_tag = serializers.CharField(source="asset.asset_tag", read_only=True)
    asset_name = serializers.CharField(source="asset.name", read_only=True)
    employee_code = serializers.CharField(source="employee.employee_code", read_only=True)
    employee_email = serializers.EmailField(source="employee.user.email", read_only=True)
    assigned_by_email = serializers.EmailField(
        source="assigned_by.email",
        read_only=True,
        default=None,
    )

    class Meta:
        model = AssetAssignment
        fields = (
            "id",
            "asset",
            "asset_tag",
            "asset_name",
            "employee",
            "employee_code",
            "employee_email",
            "assigned_by",
            "assigned_by_email",
            "assigned_at",
            "returned_at",
            "status",
            "notes",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "assigned_by",
            "assigned_at",
            "returned_at",
            "status",
            "created_at",
            "updated_at",
        )


class AssignAssetSerializer(serializers.Serializer):
    asset_id = serializers.IntegerField()
    employee_id = serializers.IntegerField()
    notes = serializers.CharField(required=False, allow_blank=True, default="")


class ReturnAssetSerializer(serializers.Serializer):
    notes = serializers.CharField(required=False, allow_blank=True, default="")


@transaction.atomic
def assign_asset(*, asset_id: int, employee_id: int, actor, notes: str = "", request=None) -> AssetAssignment:
    asset = Asset.objects.select_for_update().get(pk=asset_id)
    employee = Employee.objects.get(pk=employee_id, is_active=True)

    if asset.status not in (Asset.Status.AVAILABLE,):
        raise ValidationError({"asset_id": f"Asset is not available (status={asset.status})."})
    if AssetAssignment.objects.filter(asset=asset, status=AssetAssignment.Status.ACTIVE).exists():
        raise ValidationError({"asset_id": "Asset already has an active assignment."})

    now = timezone.now()
    assignment = AssetAssignment.objects.create(
        asset=asset,
        employee=employee,
        assigned_by=actor,
        assigned_at=now,
        status=AssetAssignment.Status.ACTIVE,
        notes=notes or "",
    )
    asset.status = Asset.Status.ALLOCATED
    asset.save(update_fields=["status", "updated_at"])

    write_audit_log(
        actor=actor,
        action=AuditLog.Action.ASSIGN,
        entity_type="assets.AssetAssignment",
        entity_id=assignment.pk,
        changes={"asset_id": asset.id, "employee_id": employee.id},
        request=request,
    )

    owner_name = f"{employee.user.first_name} {employee.user.last_name}".strip() or employee.user.email
    msg = (
        f"{asset.asset_tag} ({asset.name}) assigned to {owner_name} "
        f"({employee.employee_code}) in {employee.department.name}."
    )
    notify_admins_and_managers(
        title="Asset assigned",
        message=msg,
        notification_type=Notification.NotificationType.ASSIGNMENT,
        link=f"/assets/{asset.id}",
        entity_type="assets.AssetAssignment",
        entity_id=assignment.pk,
        exclude_user_id=getattr(actor, "id", None),
    )
    notify_user(
        recipient=employee.user,
        title="Asset assigned to you",
        message=f"You have been assigned {asset.asset_tag} ({asset.name}).",
        notification_type=Notification.NotificationType.ASSIGNMENT,
        link=f"/assets/{asset.id}",
        entity_type="assets.Asset",
        entity_id=asset.id,
    )
    notify_admin_mailbox(
        subject=f"[AssetFlow] Asset assigned: {asset.asset_tag}",
        body=(
            f"{getattr(actor, 'email', 'system')} assigned {asset.asset_tag} "
            f"to {employee.user.email} ({employee.employee_code})."
        ),
    )
    return assignment


@transaction.atomic
def return_assignment(*, assignment: AssetAssignment, actor, notes: str = "", request=None) -> AssetAssignment:
    if assignment.status != AssetAssignment.Status.ACTIVE:
        raise ValidationError({"detail": "Only active assignments can be returned."})

    assignment.status = AssetAssignment.Status.RETURNED
    assignment.returned_at = timezone.now()
    if notes:
        assignment.notes = f"{assignment.notes}\nReturn: {notes}".strip()
    assignment.save(update_fields=["status", "returned_at", "notes", "updated_at"])

    asset = Asset.objects.select_for_update().get(pk=assignment.asset_id)
    if asset.status == Asset.Status.ALLOCATED:
        asset.status = Asset.Status.AVAILABLE
        asset.save(update_fields=["status", "updated_at"])

    write_audit_log(
        actor=actor,
        action=AuditLog.Action.RETURN,
        entity_type="assets.AssetAssignment",
        entity_id=assignment.pk,
        changes={"asset_id": asset.id, "status": assignment.status},
        request=request,
    )
    return assignment
