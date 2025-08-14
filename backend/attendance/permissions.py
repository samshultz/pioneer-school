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
        return request.method in permissions.SAFE_METHODS
    
class CanManageAttendance(permissions.BasePermission):
    """
    - Only Form Teachers of a class can create/update/delete attendance for that class.
    - Everyone else (Admin, Principal, Student, Parent) has read-only access.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        role = getattr(request.user.memberships.first(), "role", None)

        # Safe methods: all roles can view
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions: only teachers who are form teachers of the class
        if role == Membership.RoleChoices.TEACHER:
            # For viewsets where pk is passed in the URL
            if "pk" in view.kwargs:
                from attendance.models import AttendanceSession
                try:
                    session = AttendanceSession.objects.get(pk=view.kwargs["pk"])
                except AttendanceSession.DoesNotExist:
                    return False
                return session.form_teacher == request.user.memberships().teacher_profile
            return True  # fallback for other cases
        return False

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        role = getattr(request.user.memberships.first(), "role", None)

        # Teacher must be the assigned form teacher for this class
        if role == Membership.RoleChoices.TEACHER:
            # For AttendanceSession
            if hasattr(obj, "form_teacher"):
                return obj.form_teacher == request.user.memberships.first().teacher_profile
            # For AttendanceRecord
            if hasattr(obj, "session"):
                return obj.session.form_teacher == request.user.memberships().teacher_profile

        return False