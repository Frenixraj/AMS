"""Serializers for admin user management and profiles."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()

PUBLIC_ROLES = [
    User.Role.ADMIN,
    User.Role.ASSET_MANAGER,
    User.Role.MANAGER,
    User.Role.EMPLOYEE,
]


class UserListSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    has_employee_profile = serializers.SerializerMethodField()
    profile_picture_url = serializers.SerializerMethodField()
    department_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "full_name",
            "role",
            "phone",
            "address",
            "profile_picture_url",
            "is_active",
            "is_staff",
            "has_employee_profile",
            "department_name",
            "date_joined",
        )
        read_only_fields = fields

    def get_full_name(self, obj: User) -> str:
        name = f"{obj.first_name} {obj.last_name}".strip()
        return name or obj.email

    def get_has_employee_profile(self, obj: User) -> bool:
        from employees.models import Employee

        return Employee.objects.filter(user_id=obj.pk).exists()

    def get_profile_picture_url(self, obj: User) -> str | None:
        if not obj.profile_picture:
            return None
        request = self.context.get("request")
        url = obj.profile_picture.url
        if request:
            return request.build_absolute_uri(url)
        return url

    def get_department_name(self, obj: User) -> str | None:
        profile = getattr(obj, "employee_profile", None)
        if profile is None:
            return None
        return profile.department.name


class UserCreateSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(min_length=8, write_only=True)
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True, default="")
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True, default="")
    role = serializers.ChoiceField(choices=[(r.value, r.label) for r in PUBLIC_ROLES], default=User.Role.EMPLOYEE)
    phone = serializers.CharField(max_length=32, required=False, allow_blank=True, default="")
    address = serializers.CharField(required=False, allow_blank=True, default="")
    is_active = serializers.BooleanField(default=True)

    def validate_email(self, value: str) -> str:
        email = value.strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return email

    def validate_role(self, value: str) -> str:
        if value == User.Role.ASSET_MANAGER:
            if User.objects.filter(role=User.Role.ASSET_MANAGER, is_active=True).exists():
                raise serializers.ValidationError(
                    "Only one active Asset Manager is allowed. "
                    "Deactivate or delete the existing Asset Manager first."
                )
        return value

    def create(self, validated_data):
        email = validated_data["email"]
        username = email.split("@")[0][:100]
        base = username
        n = 1
        while User.objects.filter(username=username).exists():
            username = f"{base}{n}"
            n += 1

        role = validated_data.get("role", User.Role.EMPLOYEE)
        user = User.objects.create_user(
            username=username,
            email=email,
            password=validated_data["password"],
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
            role=role,
            phone=validated_data.get("phone", ""),
            address=validated_data.get("address", ""),
            is_active=validated_data.get("is_active", True),
            is_staff=role in (User.Role.ADMIN, User.Role.ASSET_MANAGER),
            is_superuser=role == User.Role.ADMIN,
        )
        return user


class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "phone", "address", "profile_picture")
