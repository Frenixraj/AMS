"""Global audit log listing for Admin / IT."""

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import serializers, viewsets
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.routers import DefaultRouter

from common.models import AuditLog
from common.permissions import IsAdminOrITTeam


class AuditLogSerializer(serializers.ModelSerializer):
    actor_email = serializers.EmailField(source="actor.email", read_only=True, default=None)

    class Meta:
        model = AuditLog
        fields = (
            "id",
            "actor",
            "actor_email",
            "action",
            "entity_type",
            "entity_id",
            "changes",
            "ip_address",
            "created_at",
        )
        read_only_fields = fields


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.select_related("actor").all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated, IsAdminOrITTeam]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ("action", "entity_type", "actor")
    search_fields = ("entity_type", "entity_id", "actor__email")
    ordering = ("-created_at",)


router = DefaultRouter()
router.register(r"audit-logs", AuditLogViewSet, basename="audit-log")
