from datetime import time
from academics.models import Class, Subject, ClassSubject, Timetable
from users.models import User, Membership, TeacherProfile
from rest_framework_simplejwt.tokens import RefreshToken


def create_user_with_role(email, role, org, password="testpass123", first_name="Test", last_name="User"):
    """
    Create a user with a given role and organization membership.
    """
    user = User.objects.create_user(
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
    )
    Membership.objects.create(user=user, organization=org, role=role)
    return user


def create_teacher_with_profile(email, organization, employee_id="EMP123"):
    from tests.utils import create_user_with_role
    from users.models import Membership

    teacher_user = create_user_with_role(email, Membership.RoleChoices.TEACHER, organization)
    profile = TeacherProfile.objects.create(
        membership=teacher_user.memberships.first(),
        employee_id=employee_id,
    )
    return profile

def login(api_client, email, password, org_id):
    """
    Logs in the user and attaches JWT token to client headers.
    """
    response = api_client.post(
        "/api/auth/login/",
        {
            "username": email, 
            "password": password, 
            "organization_id": org_id
        },
        format="json",
    )
    assert response.status_code == 200, f"Login failed: {response.data}"
    token = response.data["access"]
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return response

def create_school_class(name="JSS1A", section="A", organization=None):
    return Class.objects.create(
        name=name,
        section=section,
        year=2025,
        organization=organization,
    )

def create_subject(name="Mathematics", code="MATH101", organization=None):
    return Subject.objects.create(
        name=name,
        code=code,
        organization=organization,
    )

def create_class_subject(school_class, subject, teacher=None, organization=None):
    return ClassSubject.objects.create(
        school_class=school_class,
        subject=subject,
        teacher=teacher,
        organization=organization,
    )

def create_timetable(class_subject, day="MONDAY", start=time(9), end=time(10), room="Room 101", organization=None):
    return Timetable.objects.create(
        class_subject=class_subject,
        day_of_week=day,
        start_time=start,
        end_time=end,
        room=room,
        organization=organization,
    )
