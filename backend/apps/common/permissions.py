"""Reusable DRF permission classes for role-based access."""

from __future__ import annotations

from rest_framework.permissions import BasePermission, SAFE_METHODS


def _role(user) -> str | None:
    if not user or not user.is_authenticated:
        return None
    if user.is_superuser:
        return "ADMIN"
    return getattr(user, "role", None)


class IsAdminOrITTeam(BasePermission):
    """Write access for Admin and IT Team; others denied."""

    def has_permission(self, request, view) -> bool:
        return _role(request.user) in ("ADMIN", "IT_TEAM")


class IsAdminOrITTeamOrReadOnly(BasePermission):
    """
    Authenticated users may read.
    Only Admin / IT Team may create, update, or delete.
    """

    def has_permission(self, request, view) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        return _role(request.user) in ("ADMIN", "IT_TEAM")


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
        return _role(request.user) in ("IT_TEAM", "ADMIN")
