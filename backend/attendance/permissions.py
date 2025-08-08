from rest_framework import permissions
from users.models import Membership

class CanViewAttendance(permissions.BasePermission):
    """
    Students, parents, admins, principals can view attendance.
    Teachers can view their class sessions/records.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Read-only allowed for everyone authenticated
        if request.method in permissions.SAFE_METHODS:
            return True
        return False
    
class CanManageAttendance(permissions.BasePermission):
    """
    - Only Form Teachers of a class can create/update/delete attendance for that class.
    - Everyone else (Admin, Principal, Student, Parent) has read-only access.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        role = request.user.memberships.first().role

        # Safe methods: all roles can view
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions: only teachers who are form teachers of the class
        if role == Membership.RoleChoices.TEACHER:
            return True  # we'll refine to check form_teacher in `has_object_permission`

        return False

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        # Teacher must be the assigned form teacher for this class
        if request.user.membership.role == Membership.RoleChoices.TEACHER:
            # For AttendanceSession
            if hasattr(obj, "form_teacher"):
                return obj.form_teacher == request.user.teacher_profile
            # For AttendanceRecord
            if hasattr(obj, "session"):
                return obj.session.form_teacher == request.user.teacher_profile

        return False