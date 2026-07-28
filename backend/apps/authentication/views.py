from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication.serializers import UserCreateSerializer, UserListSerializer
from common.permissions import IsAdmin, IsAdminOrITTeam

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


class UserListCreateView(APIView):
    """
    GET  — Admin / IT: list users (optional without_employee filter).
    POST — Admin only: create a login user with a role.
    """

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), IsAdmin()]
        return [IsAuthenticated(), IsAdminOrITTeam()]

    def get(self, request):
        qs = User.objects.all().order_by("email")
        without = request.query_params.get("without_employee", "").lower() in (
            "1",
            "true",
            "yes",
        )
        if without:
            qs = qs.filter(employee_profile__isnull=True, is_active=True)
        active_only = request.query_params.get("is_active", "").lower()
        if active_only in ("1", "true", "yes"):
            qs = qs.filter(is_active=True)
        elif active_only in ("0", "false", "no"):
            qs = qs.filter(is_active=False)

        data = UserListSerializer(qs[:200], many=True).data
        return Response({"count": len(data), "results": data})

    def post(self, request):
        serializer = UserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserListSerializer(user).data, status=status.HTTP_201_CREATED)


# Backward-compatible function name for older reverse lookups in tests.
users_list = UserListCreateView.as_view()
