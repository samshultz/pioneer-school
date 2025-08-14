from django.db import models
from core.managers import OrganizationManager
from django.utils import timezone

class StudentEnrollment(models.Model):
    """
    Student enrollment linking a StudentProfile to a ClassSessionAssignment.
    This preserves historical class membership per academic session.
    """
    organization = models.ForeignKey(
        "users.Organization", 
        on_delete=models.CASCADE, 
        related_name="student_enrollments"
    )
    student = models.ForeignKey(
        "users.StudentProfile", 
        on_delete=models.CASCADE, 
        related_name="enrollments"
    )
    class_assignment = models.ForeignKey(
        "academics.ClassSessionAssignment", 
        on_delete=models.CASCADE, 
        related_name="enrollments"
    )
    date_enrolled = models.DateField(default=timezone.localdate)

    objects = OrganizationManager()
    all_objects = models.Manager()

    class Meta:
        unique_together = ("organization", "student", "class_assignment")

    def __str__(self):
        return f"{self.student} -> {self.class_assignment}"
