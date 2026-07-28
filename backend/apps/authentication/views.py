from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from common.permissions import IsAdminOrITTeam

User = get_user_model()


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    """Return the authenticated user plus optional employee profile."""
    user = request.user
    payload = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "role": getattr(user, "role", None),
        "employee_profile": None,
    }

    profile = getattr(user, "employee_profile", None)
    if profile is not None:
        payload["employee_profile"] = {
            "id": profile.id,
            "employee_code": profile.employee_code,
            "department_id": profile.department_id,
            "department_name": profile.department.name,
            "job_title": profile.job_title,
            "is_active": profile.is_active,
        }

    return Response(payload)


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdminOrITTeam])
def users_list(request):
    """
    List users for admin/IT (e.g. linking an Employee profile).
    Query: without_employee=true — only users that have no Employee row.
    """
    qs = User.objects.filter(is_active=True).order_by("email")
    without = request.query_params.get("without_employee", "").lower() in (
        "1",
        "true",
        "yes",
    )
    if without:
        qs = qs.filter(employee_profile__isnull=True)

    data = [
        {
            "id": u.id,
            "email": u.email,
            "first_name": u.first_name,
            "last_name": u.last_name,
            "role": u.role,
            "full_name": f"{u.first_name} {u.last_name}".strip() or u.email,
        }
        for u in qs[:200]
    ]
    return Response({"count": len(data), "results": data})
