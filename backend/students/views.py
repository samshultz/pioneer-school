# students/views.py
from rest_framework import (
    viewsets, 
    serializers
)
from core.permissions import (
    IsAdminOrPrincipal,
    IsTeacherReadOnly,
    IsStudentSelfOnly,
    any_of
)
from users.models import StudentProfile, Membership
from .serializers import StudentProfileSerializer


class StudentProfileViewSet(viewsets.ModelViewSet):
    queryset = StudentProfile.objects.all()
    serializer_class = StudentProfileSerializer
    permission_classes = [
        any_of(
            IsAdminOrPrincipal, 
            IsTeacherReadOnly, 
            IsStudentSelfOnly
        )
    ]

    def get_queryset(self):
        user = self.request.user
        org = getattr(self.request, "organization", None)

        # Unauthenticated → no queryset
        if not user.is_authenticated or not org:
            return StudentProfile.objects.none()

        # Admins & Principals → can view all
        if Membership.objects.filter(
            user=user,
            organization=org,
            role__in=[Membership.RoleChoices.ADMIN, Membership.RoleChoices.PRINCIPAL],
            is_active=True
        ).exists():
            return StudentProfile.objects.all()

        # Teachers → can view all (read-only already enforced in permissions)
        if Membership.objects.filter(
            user=user,
            organization=org,
            role=Membership.RoleChoices.TEACHER,
            is_active=True
        ).exists():
            return StudentProfile.objects.all()

        # Students → only their own profile
        student_membership = Membership.objects.filter(
            user=user,
            organization=org,
            role=Membership.RoleChoices.STUDENT,
            is_active=True
        ).first()
        if student_membership:
            return StudentProfile.objects.filter(membership=student_membership)

        # Default → nothing
        return StudentProfile.objects.none()
    
    def perform_create(self, serializer):
        org = getattr(self.request, "organization", None)
        if not org:
            raise serializers.ValidationError("Organization context required")
        serializer.save()