"""URL routing for the Asset Management module."""

from django.urls import include, path
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.routers import DefaultRouter

from assets.views import (
    AssetAssignmentViewSet,
    AssetCategoryViewSet,
    AssetViewSet,
    VendorViewSet,
)

router = DefaultRouter()
router.register(r"categories", AssetCategoryViewSet, basename="asset-category")
router.register(r"vendors", VendorViewSet, basename="vendor")
router.register(r"assignments", AssetAssignmentViewSet, basename="asset-assignment")
router.register(r"", AssetViewSet, basename="asset")


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    return Response({"status": "ok", "app": "assets"})


urlpatterns = [
    path("health/", health_check, name="assets-health"),
    path("", include(router.urls)),
]
