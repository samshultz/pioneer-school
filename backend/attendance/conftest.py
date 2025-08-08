from rest_framework.test import APIClient
import pytest
from datetime import date
from django.contrib.auth import get_user_model
from users.models import (
    Organization, 
    Membership, 
    StudentProfile, 
    TeacherProfile
)
from academics.models import Class, Term, AcademicSession
from attendance.models import AttendanceSession, AttendanceRecord
from tests.utils import (
    create_teacher_with_profile, 
    create_user_with_role,
    create_school_class
)
User = get_user_model()


@pytest.fixture
def org(db):
    return Organization.objects.create(name="Test School")


@pytest.fixture
def admin_user(org):
    user = User.objects.create_user(
        username="admin", 
        password="pass", 
        is_superuser=True)
    Membership.objects.create(
        user=user, 
        organization=org, 
        role=Membership.RoleChoices.ADMIN)
    return user


@pytest.fixture
def teacher(org):
    
    # user = User.objects.create_user(username="teacher", password="pass")
    # membership = Membership.objects.create(user=user, organization=org, role=Membership.RoleChoices.TEACHER)
    teacher_profile = create_teacher_with_profile("teach320@test.com", organization=org)
    return teacher_profile


@pytest.fixture
def student(org, school_class):
    user = create_user_with_role(
        "test123@test.com", 
        role=Membership.RoleChoices.STUDENT,
        org=org,
        password="pass"
    )
    m1 = Membership.objects.get(id=user.id)
    # user = User.objects.create_user(
    #     username="student", 
    #     password="pass")
    # Membership.objects.create(user=user, organization=org, role=Membership.RoleChoices.STUDENT)
    return StudentProfile.objects.create(membership=m1, grade="JSS1")


@pytest.fixture
def student_other_class(org):
    school_class = create_school_class(
        name="JSS2",
        organization=org
    )
    user = create_user_with_role(
        "test124@test.com", 
        role=Membership.RoleChoices.STUDENT,
        org=org,
        password="pass"
    )
    m1 = Membership.objects.get(id=user.id)
    # school_class = Class.objects.create(
    #     name="JSS2", organization=org)
    # user = User.objects.create_user(
    #     username="student2", password="pass")
    # Membership.objects.create(user=user, organization=org, role=Membership.RoleChoices.STUDENT)
    return StudentProfile.objects.create(membership=m1, grade="SSS1")


@pytest.fixture
def school_class(org, teacher):
    return create_school_class(
        name="JSS1",
        organization=org
    )
    # return Class.objects.create(name="JSS1", organization=org, form_teacher=teacher)


@pytest.fixture
def term(org):
    session = AcademicSession.objects.create(
        organization=org,
        name="2025/2026",
        start_date=date(2025, 9, 8),
        end_date=date(2026, 7, 31),
    )
    return Term.objects.create(
        organization=org,
        name="First Term",
        start_date=date(2025, 1, 1),
        end_date=date(2025, 3, 31),
        session=session
    )


@pytest.fixture
def session(org, school_class, teacher, term):
    return AttendanceSession.objects.create(
        organization=org,
        class_ref=school_class,
        date=date.today(),
        period="MORNING",
        term=term,
        form_teacher=teacher,
    )


@pytest.fixture
def session_present(org, session, student, teacher):
    return AttendanceRecord.objects.create(
        organization=org, 
        session=session, 
        student=student, 
        status="PRESENT", 
        marked_by=teacher.membership.user
    )

@pytest.fixture
def api_client_teacher(teacher):
    client = APIClient()
    client.force_authenticate(user=teacher.membership.user)
    return client

@pytest.fixture
def api_client_student(student):
    client = APIClient()
    client.force_authenticate(user=student.membership.user)
    return client

@pytest.fixture
def students(org, school_class):
    """Return multiple students for bulk record tests."""
    s_list = []
    for i in range(3):
        user = create_user_with_role(
            f"test123{i}@test.com", 
            role=Membership.RoleChoices.STUDENT,
            org=org,
            password="pass",
            first_name=f"student{i}",
            last_name=f"student{i} last"

        )
        m1 = Membership.objects.get(id=user.id)
        # user = User.objects.create_user(username=f"student{i}", password="pass")
        StudentProfile.objects.create(membership=m1, grade="Grade 12")
        s_list.append(StudentProfile.objects.get(membership=m1))
    return s_list