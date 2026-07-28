"""API views for the approval workflow."""

from django.db.models import Prefetch, Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from approvals.filters import AssetRequestFilter
from approvals.models import Approval, AssetRequest
from approvals.serializers import (
    AssetRequestCreateSerializer,
    AssetRequestListSerializer,
    AssetRequestSerializer,
    DecisionSerializer,
    FulfillSerializer,
)
from approvals.services import (
    approve_request,
    cancel_request,
    create_asset_request,
    fulfill_request,
    reject_request,
)
from authentication.models import User
from common.models import AuditLog


class AssetRequestViewSet(viewsets.ModelViewSet):
    """
    Employee request → Manager approve/reject → IT allocate.

    list/retrieve: role-scoped
    create: employees with a profile
    approve/reject: department manager or admin
    fulfill: IT / admin
    cancel: requester or admin
    """

    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = AssetRequestFilter
    search_fields = (
        "request_number",
        "justification",
        "requested_by__employee_code",
        "requested_by__user__email",
        "asset__asset_tag",
    )
    ordering_fields = ("created_at", "priority", "status", "fulfilled_at")
    ordering = ("-created_at",)
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        qs = (
            AssetRequest.objects.select_related(
                "requested_by",
                "requested_by__user",
                "requested_by__department",
                "requested_by__department__manager",
                "category",
                "asset",
                "fulfilled_by",
                "assignment",
            )
            .prefetch_related(
                Prefetch(
                    "approvals",
                    queryset=Approval.objects.select_related("approver").order_by("step"),
                )
            )
            .all()
        )
        user = self.request.user
        if user.is_superuser or user.role == User.Role.ADMIN:
            return qs
        if user.role == User.Role.IT_TEAM:
            return qs
        if user.role == User.Role.MANAGER:
            return qs.filter(
                Q(requested_by__department__manager=user)
                | Q(approvals__approver=user)
            ).distinct()
        if hasattr(user, "employee_profile"):
            return qs.filter(requested_by=user.employee_profile)
        return qs.none()

    def get_serializer_class(self):
        if self.action == "list":
            return AssetRequestListSerializer
        if self.action == "create":
            return AssetRequestCreateSerializer
        return AssetRequestSerializer

    def create(self, request, *args, **kwargs):
        if not hasattr(request.user, "employee_profile"):
            return Response(
                {"detail": "An employee profile is required to submit requests."},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = AssetRequestCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        request_obj = create_asset_request(
            employee=request.user.employee_profile,
            category_id=data.get("category"),
            asset_id=data.get("asset"),
            justification=data["justification"],
            priority=data.get("priority", AssetRequest.Priority.MEDIUM),
            actor=request.user,
            http_request=request,
        )
        out = AssetRequestSerializer(request_obj, context={"request": request})
        return Response(out.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        request_obj = self.get_object()
        serializer = DecisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        updated = approve_request(
            request_obj=request_obj,
            actor=request.user,
            comments=serializer.validated_data.get("comments", ""),
            http_request=request,
        )
        return Response(AssetRequestSerializer(updated, context={"request": request}).data)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        request_obj = self.get_object()
        serializer = DecisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        updated = reject_request(
            request_obj=request_obj,
            actor=request.user,
            comments=serializer.validated_data.get("comments", ""),
            http_request=request,
        )
        return Response(AssetRequestSerializer(updated, context={"request": request}).data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        request_obj = self.get_object()
        updated = cancel_request(
            request_obj=request_obj,
            actor=request.user,
            http_request=request,
        )
        return Response(AssetRequestSerializer(updated, context={"request": request}).data)

    @action(detail=True, methods=["post"])
    def fulfill(self, request, pk=None):
        request_obj = self.get_object()
        serializer = FulfillSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        updated = fulfill_request(
            request_obj=request_obj,
            actor=request.user,
            asset_id=serializer.validated_data.get("asset_id"),
            notes=serializer.validated_data.get("notes", ""),
            http_request=request,
        )
        return Response(AssetRequestSerializer(updated, context={"request": request}).data)

    @action(detail=True, methods=["get"], url_path="audit-logs")
    def audit_logs(self, request, pk=None):
        request_obj = self.get_object()
        logs = (
            AuditLog.objects.filter(
                entity_type="approvals.AssetRequest",
                entity_id=str(request_obj.pk),
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
                "created_at": log.created_at,
            }
            for log in logs
        ]
        return Response(data)
