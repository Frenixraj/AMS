"""Notifications API for the current user."""

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from notifications.models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = (
            "id",
            "title",
            "message",
            "notification_type",
            "is_read",
            "link",
            "entity_type",
            "entity_id",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    return Response({"status": "ok", "app": "notifications"})


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ("is_read", "notification_type")
    ordering = ("-created_at",)

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)

    @action(detail=False, methods=["get"])
    def unread_count(self, request):
        count = self.get_queryset().filter(is_read=False).count()
        return Response({"unread_count": count})

    @action(detail=True, methods=["post"])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save(update_fields=["is_read", "updated_at"])
        return Response(NotificationSerializer(notification).data)

    @action(detail=False, methods=["post"])
    def mark_all_read(self, request):
        updated = self.get_queryset().filter(is_read=False).update(is_read=True)
        return Response({"updated": updated}, status=status.HTTP_200_OK)
