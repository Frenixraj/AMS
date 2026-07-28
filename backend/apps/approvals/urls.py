"""URL routing for the approval workflow."""

from django.urls import include, path
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.routers import DefaultRouter

from approvals.views import AssetRequestViewSet

router = DefaultRouter()
router.register(r"requests", AssetRequestViewSet, basename="asset-request")


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    return Response({"status": "ok", "app": "approvals"})


urlpatterns = [
    path("health/", health_check, name="approvals-health"),
    path("", include(router.urls)),
]
