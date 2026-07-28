"""Approval workflow business logic."""

from __future__ import annotations

from typing import Any

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from approvals.models import Approval, AssetRequest
from assets.models import Asset, AssetAssignment
from authentication.models import User
from common.models import AuditLog
from common.utils import write_audit_log
from notifications.models import Notification
from notifications.services import notify_admin_mailbox, notify_user

ENTITY_TYPE = "approvals.AssetRequest"


def generate_request_number() -> str:
    """Generate a unique request number: REQ-YYYYMMDD-XXXX."""
    today = timezone.localdate().strftime("%Y%m%d")
    prefix = f"REQ-{today}-"
    last = (
        AssetRequest.objects.filter(request_number__startswith=prefix)
        .order_by("-request_number")
        .values_list("request_number", flat=True)
        .first()
    )
    if last:
        try:
            seq = int(last.rsplit("-", 1)[-1]) + 1
        except ValueError:
            seq = 1
    else:
        seq = 1
    return f"{prefix}{seq:04d}"


def resolve_approver(employee) -> User | None:
    """Prefer department manager; fall back to first active Admin."""
    manager = getattr(employee.department, "manager", None)
    if manager and manager.is_active:
        return manager
    return (
        User.objects.filter(role=User.Role.ADMIN, is_active=True)
        .order_by("id")
        .first()
    )


def build_timeline(asset_request: AssetRequest) -> list[dict[str, Any]]:
    """Status timeline for UI (submitted → approval → allocation)."""
    events: list[dict[str, Any]] = [
        {
            "key": "submitted",
            "label": "Request submitted",
            "status": "done",
            "at": asset_request.created_at,
            "actor": asset_request.requested_by.user.email,
            "detail": f"Priority {asset_request.priority}",
        }
    ]

    if asset_request.status == AssetRequest.Status.CANCELLED:
        events.append(
            {
                "key": "cancelled",
                "label": "Request cancelled",
                "status": "done",
                "at": asset_request.updated_at,
                "actor": asset_request.requested_by.user.email,
                "detail": "Cancelled by requester",
            }
        )
        return events

    approval = asset_request.approvals.order_by("step").first()
    if approval:
        if approval.decision == Approval.Decision.PENDING:
            events.append(
                {
                    "key": "approval",
                    "label": "Awaiting manager decision",
                    "status": "current",
                    "at": None,
                    "actor": approval.approver.email if approval.approver else None,
                    "detail": "Pending approval",
                }
            )
        elif approval.decision == Approval.Decision.APPROVED:
            events.append(
                {
                    "key": "approved",
                    "label": "Approved by manager",
                    "status": "done",
                    "at": approval.decided_at,
                    "actor": approval.approver.email if approval.approver else None,
                    "detail": approval.comments or "Approved",
                }
            )
        elif approval.decision == Approval.Decision.REJECTED:
            events.append(
                {
                    "key": "rejected",
                    "label": "Rejected by manager",
                    "status": "done",
                    "at": approval.decided_at,
                    "actor": approval.approver.email if approval.approver else None,
                    "detail": approval.comments or "Rejected",
                }
            )
            return events

    if asset_request.status == AssetRequest.Status.APPROVED:
        events.append(
            {
                "key": "allocation",
                "label": "Awaiting IT allocation",
                "status": "current",
                "at": None,
                "actor": None,
                "detail": "IT Team will assign an available asset",
            }
        )
    elif asset_request.status == AssetRequest.Status.FULFILLED:
        events.append(
            {
                "key": "fulfilled",
                "label": "Asset allocated",
                "status": "done",
                "at": asset_request.fulfilled_at,
                "actor": asset_request.fulfilled_by.email
                if asset_request.fulfilled_by
                else None,
                "detail": (
                    f"Assigned {asset_request.asset.asset_tag}"
                    if asset_request.asset_id
                    else "Fulfilled"
                ),
            }
        )
    elif asset_request.status == AssetRequest.Status.PENDING and not approval:
        events.append(
            {
                "key": "approval",
                "label": "Awaiting manager decision",
                "status": "current",
                "at": None,
                "actor": None,
                "detail": "No approval step configured",
            }
        )

    return events


def _audit(actor, action: str, request_obj: AssetRequest, changes: dict, http_request=None):
    write_audit_log(
        actor=actor,
        action=action,
        entity_type=ENTITY_TYPE,
        entity_id=request_obj.pk,
        changes=changes,
        request=http_request,
    )


@transaction.atomic
def create_asset_request(
    *,
    employee,
    category_id: int | None,
    asset_id: int | None,
    justification: str,
    priority: str,
    actor,
    http_request=None,
) -> AssetRequest:
    if not category_id and not asset_id:
        raise ValidationError(
            {"non_field_errors": ["Provide a category and/or a specific asset."]}
        )

    asset = None
    if asset_id:
        try:
            asset = Asset.objects.select_for_update().get(pk=asset_id)
        except Asset.DoesNotExist as exc:
            raise ValidationError({"asset": "Asset not found."}) from exc
        if asset.status != Asset.Status.AVAILABLE:
            raise ValidationError(
                {"asset": f"Asset is not available (status={asset.status})."}
            )

    request_obj = AssetRequest.objects.create(
        request_number=generate_request_number(),
        requested_by=employee,
        category_id=category_id or (asset.category_id if asset else None),
        asset=asset,
        justification=justification,
        priority=priority or AssetRequest.Priority.MEDIUM,
        status=AssetRequest.Status.PENDING,
    )

    approver = resolve_approver(employee)
    Approval.objects.create(
        asset_request=request_obj,
        approver=approver,
        step=1,
        decision=Approval.Decision.PENDING,
    )

    if asset:
        asset.status = Asset.Status.REQUESTED
        asset.save(update_fields=["status", "updated_at"])
        _audit(
            actor,
            AuditLog.Action.STATUS_CHANGE,
            request_obj,
            {"asset_id": asset.id, "status": Asset.Status.REQUESTED},
            http_request,
        )

    _audit(
        actor,
        AuditLog.Action.CREATE,
        request_obj,
        {
            "request_number": request_obj.request_number,
            "status": request_obj.status,
            "category_id": request_obj.category_id,
            "asset_id": request_obj.asset_id,
        },
        http_request,
    )

    # Notify manager / admin
    if approver:
        notify_user(
            recipient=approver,
            title=f"Asset request {request_obj.request_number}",
            message=(
                f"{employee.user.email} requested an asset "
                f"(priority {request_obj.priority})."
            ),
            notification_type=Notification.NotificationType.APPROVAL,
            link=f"/approvals/{request_obj.id}",
            entity_type=ENTITY_TYPE,
            entity_id=request_obj.pk,
            email_subject=f"[AssetFlow] Approval needed: {request_obj.request_number}",
        )

    # Notify IT / Asset Manager of new pending request
    for it_user in User.objects.filter(
        role__in=[User.Role.ASSET_MANAGER, User.Role.IT_TEAM, User.Role.ADMIN],
        is_active=True,
    ):
        if approver and it_user.id == approver.id:
            continue
        notify_user(
            recipient=it_user,
            title=f"New request {request_obj.request_number}",
            message="A new asset request is pending approval.",
            notification_type=Notification.NotificationType.REQUEST,
            link=f"/approvals/{request_obj.id}",
            entity_type=ENTITY_TYPE,
            entity_id=request_obj.pk,
            email_subject=f"[AssetFlow] New request {request_obj.request_number}",
        )

    return request_obj


def _get_pending_approval(request_obj: AssetRequest) -> Approval:
    approval = request_obj.approvals.filter(decision=Approval.Decision.PENDING).first()
    if not approval:
        raise ValidationError({"detail": "No pending approval step for this request."})
    return approval


def _can_decide(user, request_obj: AssetRequest) -> bool:
    if user.is_superuser or user.role == User.Role.ADMIN:
        return True
    if user.role != User.Role.MANAGER:
        return False
    dept_manager = request_obj.requested_by.department.manager_id
    return dept_manager == user.id


@transaction.atomic
def approve_request(
    *,
    request_obj: AssetRequest,
    actor,
    comments: str = "",
    http_request=None,
) -> AssetRequest:
    """
    Manager/Admin approval. When an asset is selected (or one can be chosen),
    assign it to the requester immediately and mark the request FULFILLED.
    """
    if request_obj.status != AssetRequest.Status.PENDING:
        raise ValidationError({"detail": "Only pending requests can be approved."})
    if not _can_decide(actor, request_obj):
        raise PermissionDenied("You are not allowed to approve this request.")

    approval = _get_pending_approval(request_obj)
    approval.decision = Approval.Decision.APPROVED
    approval.comments = comments or ""
    approval.decided_at = timezone.now()
    if approval.approver_id is None:
        approval.approver = actor
    approval.save(
        update_fields=["decision", "comments", "decided_at", "approver", "updated_at"]
    )

    _audit(
        actor,
        AuditLog.Action.APPROVE,
        request_obj,
        {"comments": comments},
        http_request,
    )

    # Resolve asset to assign
    target_asset_id = request_obj.asset_id
    if not target_asset_id and request_obj.category_id:
        available = (
            Asset.objects.select_for_update()
            .filter(category_id=request_obj.category_id, status=Asset.Status.AVAILABLE)
            .order_by("asset_tag")
            .first()
        )
        if available:
            target_asset_id = available.id

    if not target_asset_id:
        # No asset to assign yet — leave APPROVED for later allocation
        request_obj.status = AssetRequest.Status.APPROVED
        request_obj.save(update_fields=["status", "updated_at"])
        notify_user(
            recipient=request_obj.requested_by.user,
            title=f"{request_obj.request_number} approved",
            message="Your request was approved. An asset will be allocated shortly.",
            notification_type=Notification.NotificationType.APPROVAL,
            link=f"/approvals/{request_obj.id}",
            entity_type=ENTITY_TYPE,
            entity_id=request_obj.pk,
        )
        notify_admin_mailbox(
            subject=f"[AssetFlow] Request approved (awaiting asset): {request_obj.request_number}",
            body=(
                f"{actor.email} approved {request_obj.request_number} for "
                f"{request_obj.requested_by.user.email}, but no available asset was found."
            ),
        )
        return request_obj

    # Assign immediately
    asset = Asset.objects.select_for_update().get(pk=target_asset_id)
    allowed = {Asset.Status.AVAILABLE, Asset.Status.REQUESTED}
    if asset.status not in allowed:
        raise ValidationError(
            {"asset_id": f"Asset cannot be allocated (status={asset.status})."}
        )
    if AssetAssignment.objects.filter(
        asset=asset, status=AssetAssignment.Status.ACTIVE
    ).exists():
        raise ValidationError({"asset_id": "Asset already has an active assignment."})

    now = timezone.now()
    assignment = AssetAssignment.objects.create(
        asset=asset,
        employee=request_obj.requested_by,
        assigned_by=actor,
        assigned_at=now,
        status=AssetAssignment.Status.ACTIVE,
        notes=comments or f"Approved request {request_obj.request_number}",
    )
    asset.status = Asset.Status.ALLOCATED
    asset.save(update_fields=["status", "updated_at"])

    request_obj.asset = asset
    request_obj.assignment = assignment
    request_obj.status = AssetRequest.Status.FULFILLED
    request_obj.fulfilled_at = now
    request_obj.fulfilled_by = actor
    request_obj.save(
        update_fields=[
            "asset",
            "assignment",
            "status",
            "fulfilled_at",
            "fulfilled_by",
            "updated_at",
        ]
    )

    _audit(
        actor,
        AuditLog.Action.ASSIGN,
        request_obj,
        {"asset_id": asset.id, "assignment_id": assignment.id, "status": "FULFILLED"},
        http_request,
    )

    employee_user = request_obj.requested_by.user
    notify_user(
        recipient=employee_user,
        title=f"{request_obj.request_number} approved — asset assigned",
        message=(
            f"Your request was approved. {asset.asset_tag} ({asset.name}) "
            f"has been assigned to you."
        ),
        notification_type=Notification.NotificationType.ASSIGNMENT,
        link=f"/assets/{asset.id}",
        entity_type=ENTITY_TYPE,
        entity_id=request_obj.pk,
        email_subject=f"[AssetFlow] Asset assigned: {asset.asset_tag}",
    )

    notify_admin_mailbox(
        subject=f"[AssetFlow] Asset assigned via approval: {asset.asset_tag}",
        body=(
            f"{actor.email} approved {request_obj.request_number} and assigned "
            f"{asset.asset_tag} to {employee_user.email}."
        ),
        context={
            "request_number": request_obj.request_number,
            "asset_tag": asset.asset_tag,
            "employee": employee_user.email,
            "approver": actor.email,
        },
    )

    return request_obj


@transaction.atomic
def reject_request(
    *,
    request_obj: AssetRequest,
    actor,
    comments: str = "",
    http_request=None,
) -> AssetRequest:
    if request_obj.status != AssetRequest.Status.PENDING:
        raise ValidationError({"detail": "Only pending requests can be rejected."})
    if not _can_decide(actor, request_obj):
        raise PermissionDenied("You are not allowed to reject this request.")

    approval = _get_pending_approval(request_obj)
    approval.decision = Approval.Decision.REJECTED
    approval.comments = comments or ""
    approval.decided_at = timezone.now()
    if approval.approver_id is None:
        approval.approver = actor
    approval.save(
        update_fields=["decision", "comments", "decided_at", "approver", "updated_at"]
    )

    request_obj.status = AssetRequest.Status.REJECTED
    request_obj.save(update_fields=["status", "updated_at"])

    if request_obj.asset_id:
        asset = Asset.objects.select_for_update().get(pk=request_obj.asset_id)
        if asset.status == Asset.Status.REQUESTED:
            asset.status = Asset.Status.AVAILABLE
            asset.save(update_fields=["status", "updated_at"])

    _audit(
        actor,
        AuditLog.Action.REJECT,
        request_obj,
        {"comments": comments, "status": request_obj.status},
        http_request,
    )

    notify_user(
        recipient=request_obj.requested_by.user,
        title=f"{request_obj.request_number} rejected",
        message=comments or "Your asset request was rejected.",
        notification_type=Notification.NotificationType.APPROVAL,
        link=f"/approvals/{request_obj.id}",
        entity_type=ENTITY_TYPE,
        entity_id=request_obj.pk,
        email_subject=f"[AssetFlow] Rejected: {request_obj.request_number}",
    )
    return request_obj


@transaction.atomic
def cancel_request(
    *,
    request_obj: AssetRequest,
    actor,
    http_request=None,
) -> AssetRequest:
    if request_obj.status not in (
        AssetRequest.Status.PENDING,
        AssetRequest.Status.APPROVED,
    ):
        raise ValidationError({"detail": "This request can no longer be cancelled."})

    is_owner = (
        hasattr(actor, "employee_profile")
        and actor.employee_profile.id == request_obj.requested_by_id
    )
    is_admin = actor.is_superuser or actor.role == User.Role.ADMIN
    if not is_owner and not is_admin:
        raise PermissionDenied("Only the requester or an admin can cancel.")

    request_obj.status = AssetRequest.Status.CANCELLED
    request_obj.save(update_fields=["status", "updated_at"])

    if request_obj.asset_id:
        asset = Asset.objects.select_for_update().get(pk=request_obj.asset_id)
        if asset.status == Asset.Status.REQUESTED:
            asset.status = Asset.Status.AVAILABLE
            asset.save(update_fields=["status", "updated_at"])

    _audit(
        actor,
        AuditLog.Action.UPDATE,
        request_obj,
        {"status": AssetRequest.Status.CANCELLED},
        http_request,
    )
    return request_obj


@transaction.atomic
def fulfill_request(
    *,
    request_obj: AssetRequest,
    actor,
    asset_id: int | None = None,
    notes: str = "",
    http_request=None,
) -> AssetRequest:
    if request_obj.status != AssetRequest.Status.APPROVED:
        raise ValidationError({"detail": "Only approved requests can be fulfilled."})
    if actor.role not in (
        User.Role.ASSET_MANAGER,
        User.Role.IT_TEAM,
        User.Role.ADMIN,
    ) and not actor.is_superuser:
        raise PermissionDenied("Only Asset Manager or Admin can allocate assets.")

    target_asset_id = asset_id or request_obj.asset_id
    if not target_asset_id:
        raise ValidationError(
            {"asset_id": "Select an available asset to allocate for this request."}
        )

    asset = Asset.objects.select_for_update().get(pk=target_asset_id)

    if request_obj.asset_id and request_obj.asset_id != asset.id:
        raise ValidationError(
            {"asset_id": "This request is locked to a specific asset."}
        )

    if request_obj.category_id and asset.category_id != request_obj.category_id:
        raise ValidationError(
            {"asset_id": "Selected asset does not match the requested category."}
        )

    allowed_statuses = {Asset.Status.AVAILABLE, Asset.Status.REQUESTED}
    if asset.status not in allowed_statuses:
        raise ValidationError(
            {"asset_id": f"Asset cannot be allocated (status={asset.status})."}
        )

    # Ensure no other active assignment
    if AssetAssignment.objects.filter(asset=asset, status=AssetAssignment.Status.ACTIVE).exists():
        raise ValidationError({"asset_id": "Asset already has an active assignment."})

    now = timezone.now()
    assignment = AssetAssignment.objects.create(
        asset=asset,
        employee=request_obj.requested_by,
        assigned_by=actor,
        assigned_at=now,
        status=AssetAssignment.Status.ACTIVE,
        notes=notes or f"Fulfilled request {request_obj.request_number}",
    )

    asset.status = Asset.Status.ALLOCATED
    asset.save(update_fields=["status", "updated_at"])

    request_obj.asset = asset
    request_obj.status = AssetRequest.Status.FULFILLED
    request_obj.fulfilled_at = now
    request_obj.fulfilled_by = actor
    request_obj.assignment = assignment
    request_obj.save(
        update_fields=[
            "asset",
            "status",
            "fulfilled_at",
            "fulfilled_by",
            "assignment",
            "updated_at",
        ]
    )

    _audit(
        actor,
        AuditLog.Action.ASSIGN,
        request_obj,
        {
            "asset_id": asset.id,
            "assignment_id": assignment.id,
            "status": request_obj.status,
        },
        http_request,
    )

    notify_user(
        recipient=request_obj.requested_by.user,
        title=f"{request_obj.request_number} fulfilled",
        message=f"Asset {asset.asset_tag} ({asset.name}) has been allocated to you.",
        notification_type=Notification.NotificationType.ASSIGNMENT,
        link=f"/assets/{asset.id}",
        entity_type=ENTITY_TYPE,
        entity_id=request_obj.pk,
        email_subject=f"[AssetFlow] Allocated: {asset.asset_tag}",
    )
    return request_obj
