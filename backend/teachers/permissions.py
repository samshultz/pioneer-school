from rest_framework.permissions import BasePermission
from users.models import Membership

class IsTeacherSelfOnly(BasePermission):
    """Teachers can only view their own profile."""

    def has_object_permission(self, request, view, obj):
        user = request.user
        org = getattr(request, "organization", None)
        if not user.is_authenticated or not org:
            return False

        # Only allow if the profile belongs to the teacher's membership
        return (
            obj.membership.user_id == user.id and
            obj.membership.organization_id == org.id and
            obj.membership.role == Membership.RoleChoices.TEACHER
        )
