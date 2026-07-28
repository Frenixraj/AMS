from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication.serializers import (
    ProfileUpdateSerializer,
    UserCreateSerializer,
    UserListSerializer,
)
from common.permissions import IsAdmin, IsAdminOrAssetManager, _role
from employees.models import Employee

User = get_user_model()


def _me_payload(user, request=None) -> dict:
    picture_url = None
    if user.profile_picture:
        url = user.profile_picture.url
        picture_url = request.build_absolute_uri(url) if request else url

    payload = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "role": getattr(user, "role", None),
        "phone": user.phone,
        "address": user.address,
        "profile_picture_url": picture_url,
        "is_active": user.is_active,
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
            "phone": profile.phone or user.phone,
            "is_active": profile.is_active,
        }
    return payload


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
@parser_classes([JSONParser, FormParser, MultiPartParser])
def me(request):
    """Return / update the authenticated user's profile."""
    if request.method == "GET":
        return Response(_me_payload(request.user, request))

    serializer = ProfileUpdateSerializer(
        request.user, data=request.data, partial=True
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()
    # Keep Employee.phone in sync when present
    if "phone" in serializer.validated_data and hasattr(request.user, "employee_profile"):
        emp = request.user.employee_profile
        emp.phone = serializer.validated_data["phone"]
        emp.save(update_fields=["phone", "updated_at"])
    return Response(_me_payload(request.user, request))


class UserListCreateView(APIView):
    """
    GET  — Admin / Asset Manager: list users.
    POST — Admin only: create a login user with a role.
    """

    parser_classes = [JSONParser, FormParser, MultiPartParser]

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), IsAdmin()]
        return [IsAuthenticated(), IsAdminOrAssetManager()]

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

        data = UserListSerializer(qs[:200], many=True, context={"request": request}).data
        return Response({"count": len(data), "results": data})

    def post(self, request):
        serializer = UserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            UserListSerializer(user, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def deactivate_user(request, pk: int):
    """
    Deactivate a user account.
    Admin: any user. Manager: employees in their department only.
    """
    try:
        target = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

    actor = request.user
    role = _role(actor)

    if role == "ADMIN" or actor.is_superuser:
        pass
    elif role == "MANAGER":
        emp = Employee.objects.filter(user=target, department__manager=actor).first()
        if not emp:
            return Response(
                {"detail": "Managers may only deactivate employees in their department."},
                status=status.HTTP_403_FORBIDDEN,
            )
    else:
        return Response({"detail": "Not allowed."}, status=status.HTTP_403_FORBIDDEN)

    if target.id == actor.id:
        return Response(
            {"detail": "You cannot deactivate your own account."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    target.is_active = False
    target.save(update_fields=["is_active"])
    Employee.objects.filter(user=target).update(is_active=False)

    return Response(UserListSerializer(target, context={"request": request}).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsAdmin])
def activate_user(request, pk: int):
    try:
        target = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

    if target.role == User.Role.ASSET_MANAGER:
        if User.objects.filter(role=User.Role.ASSET_MANAGER, is_active=True).exclude(pk=target.pk).exists():
            return Response(
                {"detail": "Another active Asset Manager already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )

    target.is_active = True
    target.save(update_fields=["is_active"])
    Employee.objects.filter(user=target).update(is_active=True)
    return Response(UserListSerializer(target, context={"request": request}).data)


users_list = UserListCreateView.as_view()
