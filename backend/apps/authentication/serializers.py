"""Serializers for admin user management."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class UserListSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    has_employee_profile = serializers.SerializerMethodField()

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
            "is_active",
            "is_staff",
            "has_employee_profile",
            "date_joined",
        )
        read_only_fields = fields

    def get_full_name(self, obj: User) -> str:
        name = f"{obj.first_name} {obj.last_name}".strip()
        return name or obj.email

    def get_has_employee_profile(self, obj: User) -> bool:
        from employees.models import Employee

        return Employee.objects.filter(user_id=obj.pk).exists()


class UserCreateSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(min_length=8, write_only=True)
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True, default="")
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True, default="")
    role = serializers.ChoiceField(choices=User.Role.choices, default=User.Role.EMPLOYEE)
    is_active = serializers.BooleanField(default=True)

    def validate_email(self, value: str) -> str:
        email = value.strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return email

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
            is_active=validated_data.get("is_active", True),
            is_staff=role in (User.Role.ADMIN, User.Role.IT_TEAM),
            is_superuser=role == User.Role.ADMIN,
        )
        return user
