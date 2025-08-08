import pytest
from rest_framework import status
from rest_framework.test import APIClient
from users.models import Membership, TeacherProfile
from tests.utils import create_user_with_role, login

pytestmark = pytest.mark.django_db

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def organization():
    from users.models import Organization
    return Organization.objects.create(name="Test School")


@pytest.mark.django_db
def test_admin_can_create_teacher_profile(api_client, organization):
    admin = create_user_with_role("admin@test.com", Membership.RoleChoices.ADMIN, organization)
    teacher = create_user_with_role("teacher1@test.com", Membership.RoleChoices.TEACHER, organization)

    login(api_client, "admin@test.com", "testpass123", organization.id)

    response = api_client.post("/api/teachers/", {
        "membership_id": teacher.memberships.first().id,
        "employee_id": "EMP001",
        "specialization": "Mathematics",
        "qualifications": "BSc Math",
    }, format="json")

    assert response.status_code == status.HTTP_201_CREATED
    assert TeacherProfile.objects.filter(employee_id="EMP001").exists()


@pytest.mark.django_db
def test_admin_can_update_teacher_profile(api_client, organization):
    admin = create_user_with_role("admin2@test.com", Membership.RoleChoices.ADMIN, organization)
    teacher = create_user_with_role("teacher2@test.com", Membership.RoleChoices.TEACHER, organization)

    profile = TeacherProfile.objects.create(
        membership=teacher.memberships.first(),
        employee_id="EMP002",
        specialization="Physics"
    )

    login(api_client, "admin2@test.com", "testpass123", organization.id)

    response = api_client.patch(f"/api/teachers/{profile.id}/", {
        "specialization": "Chemistry"
    }, format="json")

    assert response.status_code == status.HTTP_200_OK
    profile.refresh_from_db()
    assert profile.specialization == "Chemistry"


@pytest.mark.django_db
def test_admin_can_delete_teacher_profile(api_client, organization):
    admin = create_user_with_role("admin3@test.com", Membership.RoleChoices.ADMIN, organization)
    teacher = create_user_with_role("teacher3@test.com", Membership.RoleChoices.TEACHER, organization)

    profile = TeacherProfile.objects.create(
        membership=teacher.memberships.first(),
        employee_id="EMP003",
    )

    login(api_client, "admin3@test.com", "testpass123", organization.id)
    response = api_client.delete(f"/api/teachers/{profile.id}/")

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert TeacherProfile.objects.filter(id=profile.id).count() == 0


@pytest.mark.django_db
def test_teacher_can_view_own_profile(api_client, organization):
    teacher = create_user_with_role("teacher4@test.com", Membership.RoleChoices.TEACHER, organization)

    profile = TeacherProfile.objects.create(
        membership=teacher.memberships.first(),
        employee_id="EMP004",
        specialization="English"
    )

    login(api_client, "teacher4@test.com", "testpass123", organization.id)

    response = api_client.get(f"/api/teachers/{profile.id}/")
    assert response.status_code == status.HTTP_200_OK
    assert response.data["specialization"] == "English"


@pytest.mark.django_db
def test_teacher_cannot_view_other_teacher_profile(api_client, organization):
    teacher1 = create_user_with_role("teacher5@test.com", Membership.RoleChoices.TEACHER, organization)
    teacher2 = create_user_with_role("teacher6@test.com", Membership.RoleChoices.TEACHER, organization)

    profile1 = TeacherProfile.objects.create(
        membership=teacher1.memberships.first(),
        employee_id="EMP005"
    )
    profile2 = TeacherProfile.objects.create(
        membership=teacher2.memberships.first(),
        employee_id="EMP006"
    )

    login(api_client, "teacher5@test.com", "testpass123", organization.id)

    # Can view self
    resp1 = api_client.get(f"/api/teachers/{profile1.id}/")
    assert resp1.status_code == status.HTTP_200_OK

    # Cannot view other
    resp2 = api_client.get(f"/api/teachers/{profile2.id}/")
    assert resp2.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]


@pytest.mark.django_db
def test_teacher_cannot_create_update_or_delete(api_client, organization):
    teacher = create_user_with_role("teacher7@test.com", Membership.RoleChoices.TEACHER, organization)

    profile = TeacherProfile.objects.create(
        membership=teacher.memberships.first(),
        employee_id="EMP007",
    )

    login(api_client, "teacher7@test.com", "testpass123", organization.id)

    # Try create
    resp1 = api_client.post("/api/teachers/", {
        "membership_id": teacher.memberships.first().id,
        "employee_id": "EMP_NEW",
        "specialization": "Biology",
    }, format="json")
    assert resp1.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]

    # Try update
    resp2 = api_client.patch(f"/api/teachers/{profile.id}/", {
        "specialization": "Geography"
    }, format="json")
    assert resp2.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]

    # Try delete
    resp3 = api_client.delete(f"/api/teachers/{profile.id}/")
    assert resp3.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]

@pytest.mark.django_db
def test_admin_can_list_all_teachers(api_client, organization):
    admin = create_user_with_role("admin_list@test.com", Membership.RoleChoices.ADMIN, organization)
    t1 = create_user_with_role("list_t1@test.com", Membership.RoleChoices.TEACHER, organization)
    t2 = create_user_with_role("list_t2@test.com", Membership.RoleChoices.TEACHER, organization)

    TeacherProfile.objects.create(membership=t1.memberships.first(), employee_id="EMP101")
    TeacherProfile.objects.create(membership=t2.memberships.first(), employee_id="EMP102")

    login(api_client, "admin_list@test.com", "testpass123", organization.id)

    response = api_client.get("/api/teachers/")
    assert response.status_code == 200
    ids = [t["employee_id"] for t in response.data]
    assert "EMP101" in ids
    assert "EMP102" in ids


@pytest.mark.django_db
def test_teacher_can_only_list_self(api_client, organization):
    t1 = create_user_with_role("list_self1@test.com", Membership.RoleChoices.TEACHER, organization)
    t2 = create_user_with_role("list_self2@test.com", Membership.RoleChoices.TEACHER, organization)

    TeacherProfile.objects.create(membership=t1.memberships.first(), employee_id="EMP201")
    TeacherProfile.objects.create(membership=t2.memberships.first(), employee_id="EMP202")

    login(api_client, "list_self1@test.com", "testpass123", organization.id)

    response = api_client.get("/api/teachers/")
    assert response.status_code == 200
    ids = [t["employee_id"] for t in response.data]

    # Should only see own
    assert "EMP201" in ids
    assert "EMP202" not in ids
    assert len(ids) == 1
