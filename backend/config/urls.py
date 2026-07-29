"""
Root URL configuration for AssetFlow.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from common.audit_api import router as audit_router

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", include("common.urls")),
    path("api/", include(audit_router.urls)),
    path("api/auth/", include("authentication.urls")),
    path("api/assets/", include("assets.urls")),
    path("api/employees/", include("employees.urls")),
    path("api/approvals/", include("approvals.urls")),
    path("api/maintenance/", include("maintenance.urls")),
    path("api/notifications/", include("notifications.urls")),
    path("api/reports/", include("reports.urls")),
    path("api/dashboard/", include("dashboard.urls")),
]

# Serve uploaded media in Docker / local (use object storage in large production deploys).
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
