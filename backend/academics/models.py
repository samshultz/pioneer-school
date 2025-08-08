from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from users.models import Membership, Organization
from core.managers import OrganizationManager

class Class(models.Model):
    """
    Represents a school class (e.g., Grade 5, JSS2, SS1).
    """
    organization = models.ForeignKey(
        "users.Organization",  # adjust import path if needed
        on_delete=models.CASCADE,
        related_name="classes"
    )
    name = models.CharField(max_length=100)   # "Grade 5", "SS2"
    section = models.CharField(max_length=100, blank=True, null=True)  # e.g., "Science", "Arts"
    year = models.IntegerField(blank=True, null=True)  # Optional academic year
    created_at = models.DateTimeField(auto_now_add=True)

    # Multi-tenant manager
    objects = OrganizationManager()
    all_objects = models.Manager()

    def __str__(self):
        return f"{self.name}{f' - {self.section}' if self.section else ''}"


class Subject(models.Model):
    """
    Represents a school subject (e.g., Mathematics, English).
    """
    organization = models.ForeignKey(
        "users.Organization",
        on_delete=models.CASCADE,
        related_name="subjects"
    )

    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, blank=True, null=True, unique=True)  # optional subject code
    created_at = models.DateTimeField(auto_now_add=True)

    # Multi-tenant manager
    objects = OrganizationManager()
    all_objects = models.Manager()

    def __str__(self):
        return self.name


class ClassSubject(models.Model):
    """
    Junction table: Assign subjects to classes and optionally teachers.
    """

    organization = models.ForeignKey(
        "users.Organization",
        on_delete=models.CASCADE,
        related_name="class_subjects"
    )

    school_class = models.ForeignKey(Class, on_delete=models.CASCADE, related_name="class_subjects")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="class_subjects")
    teacher = models.ForeignKey(
        "users.TeacherProfile", on_delete=models.SET_NULL, blank=True, null=True, related_name="class_subjects"
    )
    # teacher = models.ForeignKey(
    #     Membership,
    #     on_delete=models.SET_NULL,
    #     null=True,
    #     blank=True,
    #     related_name="teaching_subjects",
    #     limit_choices_to={
    #         "role": Membership.RoleChoices.TEACHER},
    # )
    created_at = models.DateTimeField(default=timezone.now)

    objects = OrganizationManager()
    all_objects = models.Manager()

    class Meta:
        unique_together = ("school_class", "subject")  # Prevent duplicates

    def __str__(self):
        return f"{self.school_class} - {self.subject} ({self.teacher.user.email if self.teacher else 'Unassigned'})"


class Timetable(models.Model):
    """
    Represents a scheduled lesson for a class subject.
    """

    organization = models.ForeignKey(
        "users.Organization",
        on_delete=models.CASCADE,
        related_name="timetables"
    )
    
    class_subject = models.ForeignKey(
        "ClassSubject",
        on_delete=models.CASCADE,
        related_name="timetable_entries"
    )
    day_of_week = models.CharField(
        max_length=9,
        choices=[
            ("MONDAY", "Monday"),
            ("TUESDAY", "Tuesday"),
            ("WEDNESDAY", "Wednesday"),
            ("THURSDAY", "Thursday"),
            ("FRIDAY", "Friday"),
            ("SATURDAY", "Saturday"),
            ("SUNDAY", "Sunday"),
        ]
    )
    start_time = models.TimeField()
    end_time = models.TimeField()
    room = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Multi-tenant manager
    objects = OrganizationManager()
    all_objects = models.Manager()

    class Meta:
        unique_together = (
            "class_subject", 
            "day_of_week", 
            "start_time", 
            "end_time"
        )
        ordering = ["day_of_week", "start_time"]

    def clean(self):
        """Validate timetable rules before saving."""

        # Rule 1: start < end
        if self.start_time >= self.end_time:
            raise ValidationError(_("Start time must be before end time."))

        overlaps = Timetable.objects.filter(
            day_of_week=self.day_of_week
        ).exclude(id=self.id)

        for entry in overlaps:
            is_overlapping = self.start_time < entry.end_time and self.end_time > entry.start_time
            if not is_overlapping:
                continue

            # Rule 2: Prevent teacher conflict
            if entry.class_subject.teacher_id == self.class_subject.teacher_id:
                raise ValidationError(_("Teacher is already scheduled at this time."))

            # Rule 3: Prevent class conflict
            if entry.class_subject.school_class_id == self.class_subject.school_class_id:
                raise ValidationError(_("Class already has another subject at this time."))

            # Rule 4: Prevent room conflict
            if self.room and entry.room and self.room == entry.room:
                raise ValidationError(_("Room is already booked at this time."))

    def save(self, *args, **kwargs):
        self.clean()  # always validate before saving
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.class_subject} - {self.day_of_week} {self.start_time}-{self.end_time}"

class AcademicSession(models.Model):
    organization = models.ForeignKey(
        "users.Organization", on_delete=models.CASCADE, related_name="academic_sessions"
    )
    name = models.CharField(max_length=20)  
    # e.g. "2024/2025"
    start_date = models.DateField()
    end_date = models.DateField()

    objects = OrganizationManager()
    all_objects = models.Manager()

    class Meta:
        unique_together = ("organization", "name")
        ordering = ["-start_date"]

    def __str__(self):
        return f"{self.organization} - {self.name}"

class Term(models.Model):
    TERM_CHOICES = [
        ("FIRST", "First Term"),
        ("SECOND", "Second Term"),
        ("THIRD", "Third Term"),
    ]

    organization = models.ForeignKey(
        "users.Organization", on_delete=models.CASCADE, related_name="terms"
    )
    session = models.ForeignKey(
        AcademicSession, on_delete=models.CASCADE, related_name="terms"
    )
    name = models.CharField(max_length=10, choices=TERM_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()

    objects = OrganizationManager()
    all_objects = models.Manager()

    class Meta:
        unique_together = ("organization", "session", "name")
        ordering = ["session__start_date", "start_date"]

    def __str__(self):
        return f"{self.session.name} - {self.get_name_display()}"
    