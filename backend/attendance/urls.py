from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import (
    HolidayViewSet,
    AttendanceSessionViewSet,
    AttendanceRecordViewSet,
    WeeklyAttendanceSummaryViewSet,
    WeeklyClassAttendanceSummaryViewSet,
    TermAttendanceSummaryViewSet,
    TermClassAttendanceSummaryViewSet,
)

router = DefaultRouter()

# CRUD for holidays, sessions & records
router.register(r'holidays', HolidayViewSet, basename="holiday")
router.register(r'sessions', AttendanceSessionViewSet, basename="attendance-session")
router.register(r'records', AttendanceRecordViewSet, basename="attendance-record")

# Read-only summaries
router.register(r'weekly-summaries', WeeklyAttendanceSummaryViewSet, basename="weekly-summary")
router.register(r'weekly-class-summaries', WeeklyClassAttendanceSummaryViewSet, basename="weekly-class-summary")
router.register(r'term-summaries', TermAttendanceSummaryViewSet, basename="term-summary")
router.register(r'term-class-summaries', TermClassAttendanceSummaryViewSet, basename="term-class-summary")

urlpatterns = [
    path("", include(router.urls)),
]