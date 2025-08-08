# attendance/models.py

from django.db import models
from django.utils import timezone
from django.conf import settings
from core.managers import OrganizationManager
from academics.models import Class, Term
from users.models import StudentProfile, TeacherProfile, Organization


class Holiday(models.Model):
    """Days school is not open (attendance not required)."""
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="holidays")
    date = models.DateField()
    description = models.CharField(max_length=255, blank=True)

    objects = OrganizationManager()
    all_objects = models.Manager()

    class Meta:
        unique_together = ("organization", "date")
        ordering = ["-date"]

    def __str__(self):
        return f"{self.organization} - {self.date} ({self.description})"


class AttendanceSession(models.Model):
    """One attendance session = one class + one date + one period (morning/afternoon)."""
    PERIOD_CHOICES = [
        ("MORNING", "Morning"),
        ("AFTERNOON", "Afternoon"),
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="attendance_sessions")
    class_ref = models.ForeignKey(Class, on_delete=models.CASCADE, related_name="attendance_sessions")
    date = models.DateField()
    period = models.CharField(max_length=10, choices=PERIOD_CHOICES)
    term = models.ForeignKey(
        "academics.Term", 
        on_delete=models.CASCADE, 
        related_name="attendance_sessions"
    )
    form_teacher = models.ForeignKey(TeacherProfile, on_delete=models.CASCADE, related_name="marked_sessions")
    is_locked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = OrganizationManager()
    all_objects = models.Manager()

    class Meta:
        unique_together = ("organization", "class_ref", "date", "period")
        ordering = ["-date", "period"]

    def __str__(self):
        return f"{self.class_ref} - {self.date} ({self.period})"


class AttendanceRecord(models.Model):
    """Individual student attendance marking within a session."""
    STATUS_CHOICES = [
        ("PRESENT", "Present"),
        ("ABSENT", "Absent"),
        ("LATE", "Late"),
        ("EXCUSED", "Excused"),
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="attendance_records")
    session = models.ForeignKey(AttendanceSession, on_delete=models.CASCADE, related_name="records")
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="attendance_records")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="PRESENT")
    marked_at = models.DateTimeField(default=timezone.now)
    marked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="attendance_marked"
    )

    
    objects = OrganizationManager()
    all_objects = models.Manager()

    class Meta:
        unique_together = ("organization", "session", "student")
        ordering = ["session", "student"]

    def __str__(self):
        return f"{self.student} - {self.session} ({self.status})"


# Precomputed weekly summaries
class WeeklyAttendanceSummary(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="weekly_attendance_summaries")
    class_ref = models.ForeignKey(Class, on_delete=models.CASCADE, related_name="weekly_summaries")
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="weekly_summaries")
    week_start = models.DateField()
    week_end = models.DateField()
    term = models.ForeignKey(
        "academics.Term", 
        on_delete=models.CASCADE, 
        related_name="weekly_summaries"
    )
    total_sessions = models.PositiveIntegerField(default=0)
    attended_sessions = models.PositiveIntegerField(default=0)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)

    objects = OrganizationManager()
    all_objects = models.Manager()

    class Meta:
        unique_together = ("organization", "class_ref", "student", "week_start", "week_end")


# Precomputed term summaries
class TermAttendanceSummary(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="term_attendance_summaries")
    class_ref = models.ForeignKey(Class, on_delete=models.CASCADE, related_name="term_summaries")
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="term_summaries")
    term = models.ForeignKey("academics.Term", on_delete=models.CASCADE, related_name="attendance_summaries")
    total_sessions = models.PositiveIntegerField(default=0)
    attended_sessions = models.PositiveIntegerField(default=0)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)

    objects = OrganizationManager()
    all_objects = models.Manager()

    class Meta:
        unique_together = (
            "organization", 
            "class_ref", 
            "student", 
            
        "term")

class WeeklyClassAttendanceSummary(models.Model):
    """Precomputed totals for a whole class in a given week."""
    organization = models.ForeignKey("users.Organization", on_delete=models.CASCADE)
    class_ref = models.ForeignKey("academics.Class", on_delete=models.CASCADE)
    week_start = models.DateField()
    week_end = models.DateField()
    term = models.ForeignKey(
        "academics.Term", 
        on_delete=models.CASCADE, 
        related_name="weekly_class_summaries"
    )
    total_sessions = models.IntegerField(default=0)  # total possible sessions (students × school days)
    attended_sessions = models.IntegerField(default=0)  # total actual attended sessions
    percentage = models.FloatField(default=0.0)

    objects = OrganizationManager()
    all_objects = models.Manager()

    class Meta:
        unique_together = ("organization", "class_ref", "week_start", "week_end")

    def __str__(self):
        return f"{self.class_ref.name} [{self.week_start} - {self.week_end}]"
    

class TermClassAttendanceSummary(models.Model):
    """Precomputed totals for a whole class in a given term."""
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="term_class_attendance_summaries"
    )
    class_ref = models.ForeignKey(
        Class, on_delete=models.CASCADE, related_name="term_class_summaries"
    )
    term = models.ForeignKey("academics.Term", on_delete=models.CASCADE, related_name="term_class_attendance_summaries")
    total_sessions = models.PositiveIntegerField(default=0)  # total possible sessions for all students
    attended_sessions = models.PositiveIntegerField(default=0)  # total attended sessions for all students
    male_attendance = models.PositiveIntegerField(default=0)
    female_attendance = models.PositiveIntegerField(default=0)
    average_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)

    objects = OrganizationManager()   # auto‑filters by current org
    all_objects = models.Manager()    # unfiltered

    class Meta:
        unique_together = ("organization", "class_ref", "term")

    def __str__(self):
        return f"{self.class_ref.name} - {self.term}"