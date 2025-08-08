from rest_framework import viewsets, permissions
from django_filters.rest_framework import DjangoFilterBackend
from .models import Class, Subject, ClassSubject, Timetable
from .serializers import (
    ClassSerializer, 
    SubjectSerializer, 
    ClassSubjectSerializer,
    TimetableSerializer
)
from core.permissions import IsAdminOrPrincipal
from users.models import Membership


class ClassViewSet(viewsets.ModelViewSet):
    queryset = Class.objects.all()
    serializer_class = ClassSerializer
    permission_classes = [IsAdminOrPrincipal]

    def perform_create(self, serializer):
        org = getattr(self.request, "organization", None)
        serializer.save(organization=org)

class SubjectViewSet(viewsets.ModelViewSet):
    serializer_class = SubjectSerializer
    permission_classes = [IsAdminOrPrincipal]

    def get_queryset(self):
        user = self.request.user
        org = getattr(self.request, "organization", None)

        if not user.is_authenticated or not org:
            return Subject.objects.none()

        # Get active membership for this org
        membership = Membership.objects.filter(
            user=user, organization=org, is_active=True
        ).first()

        if not membership:
            return Subject.objects.none()
        
        # Admin/Principal: all subjects in org
        if membership.role in [
                Membership.RoleChoices.ADMIN, 
                Membership.RoleChoices.PRINCIPAL
            ]:
            return Subject.objects.all()

        # Teacher: only subjects they teach
        if membership.role == Membership.RoleChoices.TEACHER:
            teacher_profile = getattr(membership, "teacher_profile", None)
            if teacher_profile:
                return Subject.objects.filter(
                    classsubject__teacher=teacher_profile
                )
            return Subject.objects.none()

        return Subject.objects.none()
    
    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAdminOrPrincipal()]
        # Teachers can only list/view
        return [permissions.IsAuthenticated()]
    
    def perform_create(self, serializer):
        org = getattr(self.request, "organization", None)
        serializer.save(organization=org)

class ClassSubjectViewSet(viewsets.ModelViewSet):
    queryset = ClassSubject.objects.all()
    serializer_class = ClassSubjectSerializer
    permission_classes = [IsAdminOrPrincipal]

    def perform_create(self, serializer):
        org = getattr(self.request, "organization", None)
        serializer.save(organization=org)

class TimetableViewSet(viewsets.ModelViewSet):
    queryset = Timetable.objects.all()
    serializer_class = TimetableSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["class_subject__school_class", "day_of_week"]

    def get_queryset(self):
        user = self.request.user
        org = getattr(self.request, "organization", None)

        if not user.is_authenticated or not org:
            return Timetable.objects.none()

        # Get membership for this org
        membership = Membership.objects.filter(
            user=user, organization=org, is_active=True
        ).first()

        if not membership:
            return Timetable.objects.none()
        
        # Admin & Principal: see all timetables
        if membership.role in [
            Membership.RoleChoices.ADMIN, 
            Membership.RoleChoices.PRINCIPAL
        ]:
            return Timetable.objects.all()

        # Teacher: only their own subjects
        if membership.role == Membership.RoleChoices.TEACHER:
            teacher_profile = getattr(membership, "teacher_profile", None)
            if teacher_profile:    
                return Timetable.objects.filter(
                    class_subject__teacher=teacher_profile
                )
            return Timetable.objects.none()

        # Student: timetables for their class
        if membership.role == Membership.RoleChoices.STUDENT:
            student_profile = getattr(user, "student_profile", None)
            if student_profile:
                return Timetable.objects.filter(
                    class_subject__school_class=student_profile.school_class
                )

        # Parents: timetables of their children
        if membership.role == Membership.RoleChoices.PARENT:
            parent_profile = getattr(user, "parent_profile", None)
            if parent_profile and parent_profile.student:
                return Timetable.objects.filter(
                    class_subject__school_class=parent_profile.student.school_class
                )

        return Timetable.objects.none()

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAdminOrPrincipal()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        org = getattr(self.request, "organization", None)
        serializer.save(organization=org)