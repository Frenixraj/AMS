"""Reusable DRF permission classes for role-based access."""

from __future__ import annotations

from rest_framework.permissions import BasePermission, SAFE_METHODS

ASSET_OPS_ROLES = ("ADMIN", "ASSET_MANAGER", "IT_TEAM")


def _role(user) -> str | None:
    if not user or not user.is_authenticated:
        return None
    if user.is_superuser:
        return "ADMIN"
    return getattr(user, "role", None)


def is_asset_ops_role(role: str | None) -> bool:
    return role in ASSET_OPS_ROLES


class IsAdmin(BasePermission):
    """Only Admin (or Django superuser treated as ADMIN)."""

    def has_permission(self, request, view) -> bool:
        return _role(request.user) == "ADMIN"


class IsAdminOrAssetManager(BasePermission):
    """Write access for Admin and Asset Manager."""

    def has_permission(self, request, view) -> bool:
        return is_asset_ops_role(_role(request.user))


# Backwards-compatible aliases
IsAdminOrITTeam = IsAdminOrAssetManager


class IsAdminOrAssetManagerOrReadOnly(BasePermission):
    """Authenticated read; Admin / Asset Manager write."""

    def has_permission(self, request, view) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        return is_asset_ops_role(_role(request.user))


IsAdminOrITTeamOrReadOnly = IsAdminOrAssetManagerOrReadOnly


class IsAuthenticatedEmployee(BasePermission):
    """User must be authenticated and have an Employee profile."""

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return hasattr(user, "employee_profile")


class IsManagerOrAdmin(BasePermission):
    def has_permission(self, request, view) -> bool:
        return _role(request.user) in ("MANAGER", "ADMIN")


class IsITTeamOrAdmin(BasePermission):
    def has_permission(self, request, view) -> bool:
        return is_asset_ops_role(_role(request.user))
