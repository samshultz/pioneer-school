# core/permissions.py
from rest_framework.permissions import BasePermission, SAFE_METHODS
from users.models import Membership
# from core.utils import get_current_organization


# class IsAdminOrPrincipal(BasePermission):
#     """
#     Allows access only to users with ADMIN or PRINCIPAL role in the current org.
#     """
#     def has_permission(self, request, view):
        
#         if not request.user.is_authenticated:
#             return False
        
#         org = getattr(request, "organization", None) # or get_current_organization()
        
#         if not org:
#             return False

#         has_role = request.user.memberships.filter(
#             organization=org,
#             role__in=[
#                 Membership.RoleChoices.ADMIN, 
#                 Membership.RoleChoices.PRINCIPAL
#             ],
#             is_active=True
#         ).exists()

#         print(f"Membership match? {has_role}")
#         print("===============================================")

#         return has_role

class IsAdminOrPrincipal(BasePermission):
    """
    Allows access only to users with ADMIN or PRINCIPAL role in the current org.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        org = getattr(request, "organization", None)
        if not org:
            return False

        return request.user.memberships.filter(
            organization=org,
            role__in=[
                Membership.RoleChoices.ADMIN, 
                Membership.RoleChoices.PRINCIPAL],
            is_active=True,
        ).exists()

class IsTeacher(BasePermission):
    """Allow access only to Teachers in the current organization."""

    def has_permission(self, request, view):
        user = request.user
        org = getattr(request, "organization", None)

        if not user or not user.is_authenticated or not org:
            return False

        return Membership.all_objects.filter(
            user=user,
            organization=org,
            role=Membership.RoleChoices.TEACHER,
            is_active=True,
        ).exists()

class IsStudent(BasePermission):
    """Allow access only to Students in the current organization."""

    def has_permission(self, request, view):
        user = request.user
        org = getattr(request, "organization", None)

        if not user or not user.is_authenticated or not org:
            return False

        return Membership.all_objects.filter(
            user=user,
            organization=org,
            role=Membership.RoleChoices.STUDENT,
            is_active=True,
        ).exists()

class IsTeacherReadOnly(BasePermission):
    """Teachers can only view, not modify."""

    def has_permission(self, request, view):
        user = request.user
        org = getattr(request, "organization", None)
        if not user.is_authenticated or not org:
            return False

        # Teachers only allowed safe methods
        return (
            request.method in SAFE_METHODS and
            Membership.objects.filter(
                user=user,
                organization=org,
                role=Membership.RoleChoices.TEACHER,
                is_active=True
            ).exists()
        )

class IsStudentSelfOnly(BasePermission):
    """Students can only view their own profile."""

    def has_permission(self, request, view):
        user = request.user
        org = getattr(request, "organization", None)
        if not user.is_authenticated or not org:
            return False

        # Only allow SAFE_METHODS if the user is a STUDENT in this org
        return (
            request.method in SAFE_METHODS and
            Membership.objects.filter(
                user=user,
                organization=org,
                role=Membership.RoleChoices.STUDENT,
                is_active=True
            ).exists()
        )
    
    def has_object_permission(self, request, view, obj):
        user = request.user
        org = getattr(request, "organization", None)
        if not user.is_authenticated or not org:
            return False

        # Only if user is STUDENT in org and owns the profile
        return (
            obj.membership.user_id == user.id and
            obj.membership.organization_id == org.id and
            obj.membership.role == Membership.RoleChoices.STUDENT
        )

class AnyOf(BasePermission):
    """Allows if ANY of the listed permissions passes."""

    def __init__(self, *perms):
        self.perms = perms

    def has_permission(self, request, view):
        return any(p().has_permission(request, view) for p in self.perms)

    def has_object_permission(self, request, view, obj):
        return any(p().has_object_permission(request, view, obj) for p in self.perms)

# Factory function
def any_of(*perms):
    class _AnyOf(AnyOf):
        def __init__(self):
            super().__init__(*perms)
    return _AnyOf