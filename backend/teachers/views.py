from rest_framework import viewsets, serializers
from django_filters.rest_framework import DjangoFilterBackend
from users.models import TeacherProfile, Membership
from .serializers import (
    TeacherProfileSerializer, 
    TeacherProfileCreateSerializer
)
from core.permissions import IsAdminOrPrincipal,any_of
from .permissions import IsTeacherSelfOnly


class TeacherProfileViewSet(viewsets.ModelViewSet):
    """
    CRUD API for Teacher Profiles
    """
    queryset = TeacherProfile.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["employee_id", "specialization", "membership__organization"]


    def get_queryset(self):
        user = self.request.user
        org = getattr(self.request, "organization", None)

        if not user.is_authenticated or not org:
            return TeacherProfile.objects.none()

        # Admins & Principals: see all teachers in org (manager already filters by org)
        if Membership.objects.filter(
            user=user,
            organization=org,
            role__in=[Membership.RoleChoices.ADMIN, Membership.RoleChoices.PRINCIPAL],
            is_active=True,
        ).exists():
            return TeacherProfile.objects.all()

        # Teachers: only their own profile
        if Membership.objects.filter(
            user=user,
            organization=org,
            role=Membership.RoleChoices.TEACHER,
            is_active=True,
        ).exists():
            return TeacherProfile.objects.filter(membership__user=user)

        return TeacherProfile.objects.none()
    
    def get_serializer_class(self):
        if self.action in [
            "create", 
            "update", 
            "partial_update"
        ]:
            return TeacherProfileCreateSerializer
        return TeacherProfileSerializer

    permission_classes = [
        any_of(
            IsAdminOrPrincipal,
            IsTeacherSelfOnly,   # If teachers can view only their own
        )
    ]

    def get_permissions(self):
        """
        Enforce stricter rules for write operations.
        """
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAdminOrPrincipal()]  # Only admins/principals can modify
        return [any_of(IsAdminOrPrincipal, IsTeacherSelfOnly)()]

    def perform_create(self, serializer):
        org = getattr(self.request, "organization", None)
        if not org:
            raise serializers.ValidationError("Organization context required")
        serializer.save()
