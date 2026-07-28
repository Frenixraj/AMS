"""Dashboard API endpoints."""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from dashboard.services import build_dashboard_summary


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    return Response({"status": "ok", "app": "dashboard"})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def summary(request):
    """
    Aggregated KPIs, chart series, and recent audit activity for the dashboard.
    Query params:
      - warranty_days: int (default 90) — warranty expiry window
    """
    try:
        warranty_days = int(request.query_params.get("warranty_days", 90))
    except (TypeError, ValueError):
        warranty_days = 90
    warranty_days = max(1, min(warranty_days, 365))

    payload = build_dashboard_summary(warranty_days=warranty_days)
    return Response(payload)
