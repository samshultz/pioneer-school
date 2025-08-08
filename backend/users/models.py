from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser, 
    PermissionsMixin
)
from django.utils import timezone

from core.managers import OrganizationManager

from .managers import UserManager

# ----------------------------
# User Model
# ----------------------------
class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, blank=True, null=True)
    profile_picture = models.ImageField(upload_to="profiles/", blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)  # for Django admin
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    def __str__(self):
        return self.email
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self):
        return self.first_name or self.email


# ----------------------------
# Organization Model (Tenant)
# ----------------------------
class Organization(models.Model):
    name = models.CharField(max_length=255, unique=True)
    address = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    domain = models.CharField(max_length=255, blank=True, null=True)  # optional for subdomain/URL mapping
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


# ----------------------------
# Membership Model (User <-> Organization)
# ----------------------------
class Membership(models.Model):
    class RoleChoices(models.TextChoices):
        ADMIN = "ADMIN", "General Admin"
        PRINCIPAL = "PRINCIPAL", "Principal"
        TEACHER = "TEACHER", "Teacher"
        STUDENT = "STUDENT", "Student"
        PARENT = "PARENT", "Parent"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="memberships")
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="memberships")
    role = models.CharField(max_length=20, choices=RoleChoices.choices)
    
    date_joined = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    objects = OrganizationManager()
    all_objects = models.Manager()  # no filtering

    class Meta:
        unique_together = ("user", "organization", "role")  # A user can't have duplicate memberships in same org

    def __str__(self):
        return f"{self.user.email} - {self.role} @ {self.organization.name}"

class StudentProfile(models.Model):
    membership = models.OneToOneField(Membership, on_delete=models.CASCADE, related_name="student_profile")
    admission_number = models.CharField(max_length=50, unique=True, blank=True, null=True)
    grade = models.CharField(max_length=50, blank=True, null=True)  # e.g., "Grade 5", "SS2"
    section = models.CharField(max_length=50, blank=True, null=True)  # e.g., "Science", "Arts"
    parent_contact = models.CharField(max_length=20, blank=True, null=True)
    date_of_admission = models.DateField(default=timezone.localdate, blank=True, null=True)

    objects = OrganizationManager()
    all_objects = models.Manager()  # no filtering

    def __str__(self):
        return f"Student {self.membership.user.email} - {self.grade or 'No Grade'}"


class TeacherProfile(models.Model):
    membership = models.OneToOneField(Membership, on_delete=models.CASCADE, related_name="teacher_profile")
    employee_id = models.CharField(max_length=50, unique=True, blank=True, null=True)
    specialization = models.CharField(max_length=100, blank=True, null=True)  # e.g., "Mathematics"
    hire_date = models.DateField(default=timezone.localdate, blank=True, null=True)
    qualifications = models.TextField(blank=True, null=True)

    objects = OrganizationManager()
    all_objects = models.Manager()  # no filtering

    def __str__(self):
        return f"Teacher {self.membership.user.email} - {self.specialization or 'Unassigned'}"


class PrincipalProfile(models.Model):
    membership = models.OneToOneField(Membership, on_delete=models.CASCADE, related_name="principal_profile")
    office_number = models.CharField(max_length=20, blank=True, null=True)
    years_of_experience = models.PositiveIntegerField(default=0, blank=True, null=True)

    objects = OrganizationManager()
    all_objects = models.Manager()  # no filtering

    def __str__(self):
        return f"Principal {self.membership.user.email}"


class ParentProfile(models.Model):
    membership = models.OneToOneField(Membership, on_delete=models.CASCADE, related_name="parent_profile")
    occupation = models.CharField(max_length=100, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    objects = OrganizationManager()
    all_objects = models.Manager()  # no filtering

    def __str__(self):
        return f"Parent {self.membership.user.email}"


class AdminProfile(models.Model):
    membership = models.OneToOneField(Membership, on_delete=models.CASCADE, related_name="admin_profile")
    office_location = models.CharField(max_length=255, blank=True, null=True)

    objects = OrganizationManager()
    all_objects = models.Manager()  # no filtering

    def __str__(self):
        return f"Admin {self.membership.user.email}"