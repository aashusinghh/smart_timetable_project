from rest_framework import permissions
from .models import Role

class IsSuperAdmin(permissions.BasePermission):
    """
    Allows access only to Super Admins.
    """
    message = 'Access restricted to Super Administrators only.'

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return user.is_superuser or user.has_role(Role.Code.SUPER_ADMIN)


class IsBranchCoordinator(permissions.BasePermission):
    """
    Allows access to Branch Coordinators or Super Admins.
    """
    message = 'Access restricted to Branch Coordinators.'

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return (
            user.is_superuser or
            user.has_role(Role.Code.SUPER_ADMIN) or
            user.has_role(Role.Code.BRANCH_COORDINATOR)
        )


class IsProfessor(permissions.BasePermission):
    """
    Allows access to Professors (or Super Admins).
    """
    message = 'Access restricted to Faculty / Professors.'

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return (
            user.is_superuser or
            user.has_role(Role.Code.SUPER_ADMIN) or
            user.has_role(Role.Code.PROFESSOR)
        )


class IsSuperAdminOrReadOnly(permissions.BasePermission):
    """
    Allows read access to any authenticated user, but write access only to Super Admins.
    """
    message = 'Modification permitted only for Super Administrators.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_superuser or request.user.has_role(Role.Code.SUPER_ADMIN)

