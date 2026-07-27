from rest_framework import permissions
from .models import User


class IsAdminRole(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and (
            request.user.role == User.Role.ADMIN or request.user.is_superuser
        ))


class IsSupervisorRole(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and (
            request.user.role in [User.Role.ADMIN, User.Role.SUPERVISOR] or request.user.is_superuser
        ))


class IsPharmacistRole(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and (
            request.user.role in [User.Role.ADMIN, User.Role.SUPERVISOR, User.Role.PHARMACIST]
        ))
