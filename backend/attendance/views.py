from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from academics.models import Term
from users.models import StudentProfile

from .services import compute_term_summary_for_student
from .models import (
    AttendanceSession, 
    AttendanceRecord,
    WeeklyAttendanceSummary,
    WeeklyClassAttendanceSummary,
    TermAttendanceSummary,
    TermClassAttendanceSummary,
    Holiday
)
from .serializers import (
    AttendanceSessionSerializer, 
    AttendanceRecordSerializer,
    WeeklyAttendanceSummarySerializer,
    WeeklyClassAttendanceSummarySerializer, 
    TermAttendanceSummarySerializer,
    TermClassAttendanceSummarySerializer,
    HolidaySerializer
)
from .permissions import (
    CanViewAttendance,
    CanManageAttendance,
)


class HolidayViewSet(viewsets.ModelViewSet):
    serializer_class = HolidaySerializer
    permission_classes = [CanViewAttendance, CanManageAttendance]  # only admins can manage holidays
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["date"]

    def get_queryset(self):
        return Holiday.objects.all()


class AttendanceSessionViewSet(viewsets.ModelViewSet):
    serializer_class = AttendanceSessionSerializer
    permission_classes = [CanViewAttendance, CanManageAttendance]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["class_ref", "date", "period", "form_teacher"]

    # def get_permissions(self):
    #     if self.action in ["create", "update", "partial_update", "destroy"]:
    #         return [permissions.IsAuthenticated(), CanManageAttendance()]
    #     return [permissions.IsAuthenticated(), CanViewAttendance()]

    def get_queryset(self):
        qs = AttendanceSession.objects.all()

        # Teachers → see only their sessions
        if hasattr(self.request.user, "teacher_profile"):
            qs = qs.filter(form_teacher=self.request.user.teacher_profile)

        # Students/Parents → see only their class
        elif hasattr(self.request.user, "student_profile"):
            qs = qs.filter(class_ref=self.request.user.student_profile.class_ref)
        elif hasattr(self.request.user, "parent_profile"):
            qs = qs.filter(student__in=self.request.user.parent_profile.children.all())
        return qs
    
    @action(detail=True, methods=["post"], url_path="lock")
    def lock(self, request, pk=None):
        """Lock this session (no further edits allowed)."""
        session = self.get_object()

        if session.is_locked:
            return Response({"detail": "Session is already locked."}, status=status.HTTP_400_BAD_REQUEST)

        session.is_locked = True
        session.save(update_fields=["is_locked"])
        return Response({"detail": f"Session {session.id} locked."}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="unlock", permission_classes=[permissions.IsAdminUser])
    def unlock(self, request, pk=None):
        """Unlock session (admins only)."""
        session = self.get_object()

        if not session.is_locked:
            return Response({"detail": "Session is already unlocked."}, status=status.HTTP_400_BAD_REQUEST)

        session.is_locked = False
        session.save(update_fields=["is_locked"])
        return Response({"detail": f"Session {session.id} unlocked."}, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=["get", "post", "patch"], url_path="records")
    def records(self, request, pk=None):
        """
        GET: List all attendance records for this session.
        POST: Bulk create records (reset and replace).
        PATCH: Bulk update existing records (partial).
        """
        session = self.get_object()

        # --- LIST ---
        if session.is_locked:
            return Response(
                {
                    "detail": "This session is locked and cannot be modified",
            
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        if request.method == "GET":
            records = session.records.all()
            serializer = AttendanceRecordSerializer(records, many=True)
            return Response(serializer.data)

        # --- CREATE (RESET + REPLACE) ---
        elif request.method == "POST":
            records_data = request.data if isinstance(request.data, list) else []
            session.records.all().delete()  # reset before adding
            created_records = []
            for record in records_data:
                record["session"] = session.id
                record["organization"] = session.organization.id
                serializer = AttendanceRecordSerializer(data=record)
                serializer.is_valid(raise_exception=True)
                serializer.save(marked_by=request.user)
                created_records.append(serializer.data)
            return Response(created_records, status=status.HTTP_201_CREATED)

        # --- BULK UPDATE ---
        elif request.method == "PATCH":
            records_data = request.data if isinstance(request.data, list) else []
            updated_records = []
            for record in records_data:
                try:
                    rec_obj = session.records.get(student_id=record.get("student"))
                except AttendanceRecord.DoesNotExist:
                    return Response(
                        {"detail": f"Record not found for student {record.get('student')} in this session."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                serializer = AttendanceRecordSerializer(
                    rec_obj, data=record, partial=True
                )
                serializer.is_valid(raise_exception=True)
                serializer.save(marked_by=request.user)
                updated_records.append(serializer.data)
            return Response(updated_records, status=status.HTTP_200_OK)
    
    def perform_create(self, serializer):
        serializer.save(organization=self.request.user.membership.organization)

class AttendanceRecordViewSet(viewsets.ModelViewSet):
    serializer_class = AttendanceRecordSerializer
    permission_classes = [CanViewAttendance, CanManageAttendance]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["session", "student", "status"]

    # def get_permissions(self):
    #     if self.action in ["create", "update", "partial_update", "destroy"]:
    #         return [permissions.IsAuthenticated(), CanManageAttendance()]
    #     return [permissions.IsAuthenticated(), CanViewAttendance()]

    def get_queryset(self):
        # org = self.request.user.organization
        qs = AttendanceRecord.objects.all()

        if hasattr(self.request.user, "teacher_profile"):
            qs = qs.filter(
                session__form_teacher=self.request.user.teacher_profile
            )

        elif hasattr(self.request.user, "student_profile"):
            qs = qs.filter(
                student=self.request.user.student_profile
            )

        return qs


class WeeklyAttendanceSummaryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = WeeklyAttendanceSummarySerializer
    permission_classes = [permissions.IsAuthenticated, CanViewAttendance]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["student", "class_ref", "week_start", "week_end"]

    def get_queryset(self):
        qs = WeeklyAttendanceSummary.objects.all()

        if hasattr(self.request.user, "student_profile"):
            qs = qs.filter(student=self.request.user.student_profile)

        elif hasattr(self.request.user, "teacher_profile"):
            qs = qs.filter(class_ref__attendance_sessions__form_teacher=self.request.user.teacher_profile)

        return qs.distinct()


class TermAttendanceSummaryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TermAttendanceSummarySerializer
    permission_classes = [permissions.IsAuthenticated, CanViewAttendance]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["student", "class_ref", "term"]

    def get_queryset(self):
        qs = TermAttendanceSummary.objects.all()

        if hasattr(self.request.user, "student_profile"):
            qs = qs.filter(student=self.request.user.student_profile)

        elif hasattr(self.request.user, "teacher_profile"):
            qs = qs.filter(class_ref__attendance_sessions__form_teacher=self.request.user.teacher_profile)

        return qs.distinct()

class TermSummaryViewSet(viewsets.ViewSet):
    permission_classes = [IsAdminUser, CanViewAttendance]

    @action(detail=True, methods=["post"])
    def compute(self, request, pk=None):
        """Trigger computation for a specific term."""
        try:
            term = Term.objects.get(pk=pk, organization=request.user.membership.organization)
        except Term.DoesNotExist:
            return Response({"detail": "Term not found."}, status=404)

        for student in StudentProfile.objects.filter(organization=term.organization):
            compute_term_summary_for_student(student, student.school_class, term, term.organization)

        return Response({"detail": f"Summaries computed for term {term.id}."})
    
class WeeklyClassAttendanceSummaryViewSet(viewsets.ReadOnlyModelViewSet):
    """Allow authorized users to view precomputed weekly class summaries."""

    serializer_class = WeeklyClassAttendanceSummarySerializer
    permission_classes = [permissions.IsAuthenticated, CanViewAttendance]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["class_ref", "week_start", "week_end"]

    def get_queryset(self):
        return WeeklyClassAttendanceSummary.objects.all()

class TermClassAttendanceSummaryViewSet(viewsets.ReadOnlyModelViewSet):
    """View term class attendance summaries (read-only)."""
    serializer_class = TermClassAttendanceSummarySerializer
    permission_classes = [permissions.IsAuthenticated, CanViewAttendance]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["class_ref", "term"]

    def get_queryset(self):
        return TermClassAttendanceSummary.objects.all()