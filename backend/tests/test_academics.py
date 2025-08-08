import pytest
from rest_framework.test import APIClient
from users.models import Membership, User, Organization, TeacherProfile
from academics.models import ClassSubject
from tests.utils import (
    create_user_with_role, 
    login, 
    create_teacher_with_profile,
    create_school_class,
    create_subject,
    create_class_subject
)


@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def organization():
    from users.models import Organization
    return Organization.objects.create(name="Test School")

@pytest.mark.django_db
class TestAcademicsAPI:
    def test_admin_can_create_class_and_subject(self, api_client, organization):
        admin = create_user_with_role("admin@test.com", Membership.RoleChoices.ADMIN, organization)
        login(api_client, admin.email, "testpass123", organization.id)

        # Create Class
        resp = api_client.post("/api/academics/classes/", {"name": "Grade 5", "section": "Science"})
        assert resp.status_code == 201
        assert resp.data["name"] == "Grade 5"

        # Create Subject
        resp = api_client.post("/api/academics/subjects/", {"name": "Mathematics", "code": "MATH101"})
        assert resp.status_code == 201
        assert resp.data["name"] == "Mathematics"

    def test_teacher_cannot_create_class_or_subject(self, api_client, organization):
        teacher = create_user_with_role("teach1@test.com", Membership.RoleChoices.TEACHER, organization)
        login(api_client, teacher.email, "testpass123", organization.id)

        resp = api_client.post("/api/academics/classes/", {"name": "Grade 6"})
        assert resp.status_code == 403

        resp = api_client.post("/api/academics/subjects/", {"name": "English", "code": "ENG101"})
        assert resp.status_code == 403

    def test_admin_can_assign_subject_to_class(self, api_client, organization):
        admin = create_user_with_role("admin2@test.com", Membership.RoleChoices.ADMIN, organization)
        teacher = create_user_with_role("teach2@test.com", Membership.RoleChoices.TEACHER, organization)

        login(api_client, admin.email, "testpass123", organization.id)

        school_class = create_school_class(name="Grade 7", section="Arts", organization=organization)
        subject = create_subject(name="History", code="HIS101", organization=organization)
        teacher_profile = create_teacher_with_profile("teach320@test.com", organization)

        resp = api_client.post("/api/academics/class-subjects/", {
            "school_class": school_class.id,
            "subject": subject.id,
            "teacher": teacher_profile.id,
        })

        assert resp.status_code == 201
        assert resp.data["teacher"] == teacher_profile.id

    def test_student_cannot_assign_subject(self, api_client, organization):
        admin = create_user_with_role("admin3@test.com", Membership.RoleChoices.ADMIN, organization)
        student = create_user_with_role("stud@test.com", Membership.RoleChoices.STUDENT, organization)

        login(api_client, admin.email, "testpass123", organization.id)
        school_class = create_school_class(name="Grade 8", organization=organization)
        subject = create_subject(name="Biology", code="BIO101", organization=organization)

        login(api_client, student.email, "testpass123", organization.id)
        resp = api_client.post("/api/academics/class-subjects/", {
            "school_class": school_class.id,
            "subject": subject.id,
            # "teacher": None,
        })
        assert resp.status_code == 403

    def test_duplicate_subject_code_not_allowed(self, api_client, organization):
        admin = create_user_with_role("admin4@test.com", Membership.RoleChoices.ADMIN, organization)
        login(api_client, admin.email, "testpass123", organization.id)

        create_subject(name="Chemistry", code="CHEM101", organization=organization)

        resp = api_client.post("/api/academics/subjects/", {"name": "Chemistry2", "code": "CHEM101"})
        assert resp.status_code == 400  # Duplicate code should fail

    def test_cannot_assign_same_subject_twice_to_class(self, api_client, organization):
        admin = create_user_with_role("admin5@test.com", Membership.RoleChoices.ADMIN, organization)
        teacher = create_user_with_role("teach3@test.com", Membership.RoleChoices.TEACHER, organization)

        login(api_client, admin.email, "testpass123", organization.id)

        school_class = create_school_class(name="Grade 9", organization=organization)
        subject = create_subject(name="Geography", code="GEO101", organization=organization)
        teacher_profile = create_teacher_with_profile("teach30@test.com", organization)

        create_class_subject(
            school_class=school_class,
            subject=subject,
            teacher=teacher_profile,
            organization=organization
        )

        resp = api_client.post("/api/academics/class-subjects/", {
            "school_class": school_class.id,
            "subject": subject.id,
            "teacher": teacher.memberships.first().id,
        })

        assert resp.status_code == 400  # unique_together prevents duplicates

    def test_teacher_cannot_be_assigned_if_not_teacher_role(self, api_client, organization):
        admin = create_user_with_role("admin6@test.com", Membership.RoleChoices.ADMIN, organization)
        student = create_user_with_role("stud2@test.com", Membership.RoleChoices.STUDENT, organization)

        login(api_client, admin.email, "testpass123", organization.id)

        school_class = create_school_class(name="SS1", organization=organization)
        subject = create_subject(name="Economics", code="ECO101", organization=organization)

        resp = api_client.post("/api/academics/class-subjects/", {
            "school_class": school_class.id,
            "subject": subject.id,
            "teacher": student.memberships.first().id,
        })

        assert resp.status_code == 400  # Only teacher memberships allowed

    def test_org_isolation(self, api_client):
        org1 = Organization.objects.create(name="Org1")
        org2 = Organization.objects.create(name="Org2")

        admin1 = create_user_with_role("admin1@org1.com", Membership.RoleChoices.ADMIN, org1)
        admin2 = create_user_with_role("admin2@org2.com", Membership.RoleChoices.ADMIN, org2)

        login(api_client, admin1.email, "testpass123", org1.id)
        api_client.post("/api/academics/subjects/", {"name": "Physics", "code": "PHY101"}, format="json")

        login(api_client, admin2.email, "testpass123", org2.id)
        resp = api_client.get("/api/academics/subjects/")
        assert resp.status_code == 200
        assert all(s["name"] != "Physics" for s in resp.data)
