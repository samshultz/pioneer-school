import pytest
from rest_framework.test import APIClient
from users.models import (
    User, 
    Membership, 
    StudentProfile,
    Organization
)

pytestmark = pytest.mark.django_db

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def organization():
    from users.models import Organization
    return Organization.objects.create(name="Test School")


def login(client, email, password, org_id):
    """Helper for JWT login"""
    response = client.post("/api/auth/login/", {
        "username": email,
        "password": password,
        "organization": org_id,
    }, format="json")
    token = response.data["access"]
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}",
                       HTTP_X_ORGANIZATION_ID=str(org_id))


def create_user_with_role(email, role, org, password="testpass123"):
    user = User.objects.create_user(
        email=email, 
        password=password,
        first_name=email.split("@")[0].capitalize(),
        last_name="Test"
        )
    Membership.objects.create(
        user=user, 
        organization=org, 
        role=role,
        is_active=True
        )
    return user


### -------------------------
### Admin/Principal Permissions
### -------------------------

def test_admin_can_create_student_profile(api_client, organization):
    admin = create_user_with_role("admin@test.com", Membership.RoleChoices.ADMIN, organization)
    student = create_user_with_role("stud1@test.com", Membership.RoleChoices.STUDENT, organization)

    login(api_client, "admin@test.com", "testpass123", organization.id)

    payload = {
        "membership_id": student.memberships.first().id,
        "admission_number": "ADM001",
        "grade": "Grade 5",
        "section": "Science",
    }

    response = api_client.post("/api/students/", payload, format="json")
    assert response.status_code == 201
    assert StudentProfile.objects.filter(admission_number="ADM001").exists()


### -------------------------
### Teacher Permissions
### -------------------------

def test_teacher_cannot_create_student_profile(api_client, organization):
    teacher = create_user_with_role("teacher@test.com", Membership.RoleChoices.TEACHER, organization)
    login(api_client, "teacher@test.com", "testpass123", organization.id)

    payload = {"admission_number": "ADM002", "grade": "Grade 6"}
    response = api_client.post("/api/students/", payload, format="json")
    assert response.status_code == 403  # blocked by permission


def test_teacher_can_list_students(api_client, organization):
    teacher = create_user_with_role("teacher@test.com", Membership.RoleChoices.TEACHER, organization)
    student = create_user_with_role("stud2@test.com", Membership.RoleChoices.STUDENT, organization)
    StudentProfile.objects.create(membership=student.memberships.first(), admission_number="ADM003")

    login(api_client, "teacher@test.com", "testpass123", organization.id)
    response = api_client.get("/api/students/")
    assert response.status_code == 200
    assert len(response.data) > 0


### -------------------------
### Student Permissions
### -------------------------

def test_student_can_only_view_self(api_client, organization):
    student1 = create_user_with_role("stud3@test.com", Membership.RoleChoices.STUDENT, organization)
    student2 = create_user_with_role("stud4@test.com", Membership.RoleChoices.STUDENT, organization)

    profile1 = StudentProfile.objects.create(membership=student1.memberships.first(), admission_number="ADM004")
    profile2 = StudentProfile.objects.create(membership=student2.memberships.first(), admission_number="ADM005")

    login(api_client, "stud3@test.com", "testpass123", organization.id)

    # Can view self
    resp1 = api_client.get(f"/api/students/{profile1.id}/")
    assert resp1.status_code == 200

    # Cannot view other
    resp2 = api_client.get(f"/api/students/{profile2.id}/")
    assert resp2.status_code == 404


### -------------------------
### Admin Update & Delete Tests
### -------------------------

def test_admin_can_update_student_profile(api_client, organization):
    admin = create_user_with_role("admin2@test.com", Membership.RoleChoices.ADMIN, organization)
    student = create_user_with_role("stud_update@test.com", Membership.RoleChoices.STUDENT, organization)

    profile = StudentProfile.objects.create(
        membership=student.memberships.first(),
        admission_number="ADM100",
        grade="Grade 5",
        section="Science"
    )

    login(api_client, "admin2@test.com", "testpass123", organization.id)

    payload = {"grade": "Grade 6", "section": "Arts"}
    response = api_client.patch(f"/api/students/{profile.id}/", payload, format="json")

    assert response.status_code == 200
    profile.refresh_from_db()
    assert profile.grade == "Grade 6"
    assert profile.section == "Arts"


def test_admin_can_delete_student_profile(api_client, organization):
    admin = create_user_with_role("admin3@test.com", Membership.RoleChoices.ADMIN, organization)
    student = create_user_with_role("stud_delete@test.com", Membership.RoleChoices.STUDENT, organization)

    profile = StudentProfile.objects.create(
        membership=student.memberships.first(),
        admission_number="ADM200"
    )

    login(api_client, "admin3@test.com", "testpass123", organization.id)

    response = api_client.delete(f"/api/students/{profile.id}/")
    assert response.status_code == 204
    assert not StudentProfile.objects.filter(id=profile.id).exists()
