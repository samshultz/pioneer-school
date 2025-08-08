import pytest
from datetime import time
from tests.utils import (
    create_user_with_role,
    create_teacher_with_profile,
    create_school_class,
    create_subject,
    create_class_subject,
    create_timetable,
    login,
)
from users.models import Membership
from academics.models import Timetable

@pytest.mark.django_db
class TestTimetableAPI:
    def test_teacher_can_only_view_their_timetable(self, api_client, organization):
        teacher1 = create_teacher_with_profile("teach1@test.com", organization)
        teacher2 = create_teacher_with_profile("teach2@test.com", organization, employee_id="EMP124563")

        school_class = create_school_class(name="JSS1A", organization=organization)
        subject1 = create_subject(name="Mathematics", code="MATH101", organization=organization)
        subject2 = create_subject(name="Physics", code="PHY102", organization=organization)

        class_subject1 = create_class_subject(school_class, subject1, teacher1, organization=organization)
        class_subject2 = create_class_subject(school_class, subject2, teacher2, organization=organization)

        create_timetable(class_subject1, day="MONDAY", start=time(9), end=time(10), organization=organization)
        create_timetable(class_subject2, day="TUESDAY", start=time(9), end=time(10), organization=organization)

        # Login as teacher1
        login(api_client, teacher1.membership.user.email, "testpass123", organization.id)

        resp = api_client.get("/api/academics/timetables/")
        assert resp.status_code == 200
        results = resp.json()
        print(results)
        assert len(results) == 1
        assert results[0]["teacher_name"] == teacher1.membership.user.get_full_name()

    def test_prevent_overlapping_teacher_class_and_room(self, api_client, organization):
        admin = create_user_with_role("admin2@test.com", Membership.RoleChoices.ADMIN, organization)
        teacher_profile = create_teacher_with_profile("teach3@test.com", organization)

        school_class = create_school_class(name="JSS1B", organization=organization)
        subject = create_subject(name="Mathematics", code="MATH102", organization=organization)

        class_subject = create_class_subject(school_class, subject, teacher_profile, organization=organization)

        login(api_client, admin.email, "testpass123", organization.id)

        create_timetable(class_subject, day="MONDAY", start=time(9), end=time(10), room="Lab1", organization=organization)

        # Teacher conflict
        resp = api_client.post("/api/academics/timetables/", {
            "class_subject": class_subject.id,
            "day_of_week": "MONDAY",
            "start_time": "09:30",
            "end_time": "10:30",
            "room": "Room 202"
        }, format="json")
        assert resp.status_code == 400
        assert "Teacher is already assigned" in str(resp.data)

        # Room conflict
        resp = api_client.post("/api/academics/timetables/", {
            "class_subject": class_subject.id,
            "day_of_week": "MONDAY",
            "start_time": "09:30",
            "end_time": "10:30",
            "room": "Lab1"
        }, format="json")
        assert resp.status_code == 400
        assert "Room" in str(resp.data)

    def test_create_valid_timetable_entry(self, api_client, organization):
        admin = create_user_with_role("admin3@test.com", Membership.RoleChoices.ADMIN, organization)
        teacher_profile = create_teacher_with_profile("teach4@test.com", organization)

        school_class = create_school_class(name="JSS1C", organization=organization)
        subject = create_subject(name="English", code="ENG101", organization=organization)

        class_subject = create_class_subject(school_class, subject, teacher_profile, organization=organization)

        login(api_client, admin.email, "testpass123", organization.id)

        resp = api_client.post("/api/academics/timetables/", {
            "class_subject": class_subject.id,
            "day_of_week": "WEDNESDAY",
            "start_time": "11:00",
            "end_time": "12:00",
            "room": "Room 105"
        }, format="json")
        assert resp.status_code == 201, resp.data
        assert resp.data["day_of_week"] == "WEDNESDAY"
        assert resp.data["room"] == "Room 105"

    def test_admin_can_view_all_timetables(self, api_client, organization):
        admin = create_user_with_role("admin@test.com", Membership.RoleChoices.ADMIN, organization)
        teacher = create_teacher_with_profile("teach@test.com", organization)

        school_class = create_school_class(name="JSS1B", organization=organization)
        subject = create_subject(name="Chemistry", code="CHEM101", organization=organization)
        class_subject = create_class_subject(school_class, subject, teacher, organization=organization)

        create_timetable(class_subject, day="WEDNESDAY", start=time(8), end=time(9), organization=organization)

        login(api_client, admin.email, "testpass123", organization.id)

        resp = api_client.get("/api/academics/timetables/")
        assert resp.status_code == 200
        results = resp.json()
        assert len(results) == Timetable.objects.count()

    def test_invalid_time_range(self, api_client, organization):
        admin = create_user_with_role(
            "admin_invalid@test.com", 
            Membership.RoleChoices.ADMIN, 
            organization
        )
        teacher = create_teacher_with_profile("teach5@test.com", organization)
        school_class = create_school_class(name="JSS1E", organization=organization)
        subject = create_subject(name="History", code="HIS101", organization=organization)
        class_subject = create_class_subject(school_class, subject, teacher, organization=organization)

        login(api_client, admin.email, "testpass123", organization.id)

        resp = api_client.post("/api/academics/timetables/", {
            "class_subject": class_subject.id,
            "day_of_week": "THURSDAY",
            "start_time": "14:00",
            "end_time": "13:00",  # ❌ end before start
            "room": "Room 107"
        }, format="json")
        assert resp.status_code == 400
        assert "Start time must be before end time" in str(resp.json())

    def test_teacher_cannot_view_other_teachers_timetable(self, api_client, organization):
        teacher1 = create_teacher_with_profile("teach6@test.com", organization)
        teacher2 = create_teacher_with_profile("teach7@test.com", organization, employee_id='EMP3784')

        school_class = create_school_class(name="JSS1F", organization=organization)
        subject1 = create_subject(name="Geography", code="GEO101", organization=organization)
        subject2 = create_subject(name="Economics", code="ECO101", organization=organization)

        class_subject1 = create_class_subject(school_class, subject1, teacher1, organization=organization)
        class_subject2 = create_class_subject(school_class, subject2, teacher2, organization=organization)

        create_timetable(class_subject1, day="FRIDAY", start=time(9), end=time(10), organization=organization)
        create_timetable(class_subject2, day="FRIDAY", start=time(10), end=time(11), organization=organization)

        login(api_client, teacher1.membership.user.email, "testpass123", organization.id)

        resp = api_client.get("/api/academics/timetables/")
        results = resp.json()
        assert all(entry["teacher_name"] == teacher1.membership.user.get_full_name() for entry in results)

    def test_teacher_cannot_create_timetable(self, api_client, organization):
        """Ensure teachers are forbidden from creating timetables directly."""
        teacher = create_teacher_with_profile("teach6@test.com", organization)

        school_class = create_school_class(name="JSS1F", organization=organization)
        subject = create_subject(name="Geography", code="GEO101", organization=organization)
        class_subject = create_class_subject(school_class, subject, teacher, organization=organization)

        # Login as teacher
        login(api_client, teacher.membership.user.email, "testpass123", organization.id)

        resp = api_client.post("/api/academics/timetables/", {
            "class_subject": class_subject.id,
            "day_of_week": "FRIDAY",
            "start_time": "09:00",
            "end_time": "10:00",
            "room": "Room 108"
        }, format="json")

        assert resp.status_code == 403
        assert "permission" in str(resp.json()).lower()

    def test_admin_can_create_timetable(self, api_client, organization):
        """Ensure admins can create valid timetables successfully."""
        admin = create_user_with_role(
            "admin_valid@test.com", Membership.RoleChoices.ADMIN, organization
        )
        teacher = create_teacher_with_profile("teach7@test.com", organization)

        school_class = create_school_class(name="JSS1G", organization=organization)
        subject = create_subject(name="Biology", code="BIO101", organization=organization)
        class_subject = create_class_subject(school_class, subject, teacher, organization=organization)

        # Login as admin
        login(api_client, admin.email, "testpass123", organization.id)

        resp = api_client.post("/api/academics/timetables/", {
            "class_subject": class_subject.id,
            "day_of_week": "MONDAY",
            "start_time": "08:00",
            "end_time": "09:00",
            "room": "Room 109"
        }, format="json")

        assert resp.status_code == 201
        body = resp.json()
        assert body["class_subject"] == class_subject.id
        assert body["room"] == "Room 109"

    def test_admin_can_update_timetable(self, api_client, organization):
        """Admins should be able to update an existing timetable entry."""
        admin = create_user_with_role(
            "admin_update@test.com", Membership.RoleChoices.ADMIN, organization
        )
        teacher = create_teacher_with_profile("teach8@test.com", organization)

        school_class = create_school_class(name="JSS1H", organization=organization)
        subject = create_subject(name="Chemistry", code="CHEM101", organization=organization)
        class_subject = create_class_subject(school_class, subject, teacher, organization=organization)

        login(api_client, admin.email, "testpass123", organization.id)

        timetable = create_timetable(class_subject, day="MONDAY", start=time(8), end=time(9), organization=organization)

        resp = api_client.patch(f"/api/academics/timetables/{timetable.id}/", {
            "room": "Lab 201"
        }, format="json")

        assert resp.status_code == 200
        assert resp.json()["room"] == "Lab 201"

    def test_teacher_cannot_update_timetable(self, api_client, organization):
        """Teachers should not be allowed to update timetable entries."""
        teacher = create_teacher_with_profile("teach9@test.com", organization)

        school_class = create_school_class(name="JSS1I", organization=organization)
        subject = create_subject(name="Economics", code="ECO101", organization=organization)
        class_subject = create_class_subject(school_class, subject, teacher, organization=organization)

        timetable = create_timetable(class_subject, day="TUESDAY", start=time(10), end=time(11), organization=organization)

        login(api_client, teacher.membership.user.email, "testpass123", organization.id)

        resp = api_client.patch(f"/api/academics/timetables/{timetable.id}/", {
            "room": "Room 110"
        }, format="json")

        assert resp.status_code == 403
        assert "permission" in str(resp.json()).lower()

    def test_admin_can_delete_timetable(self, api_client, organization):
        """Admins should be able to delete timetable entries."""
        admin = create_user_with_role(
            "admin_delete@test.com", Membership.RoleChoices.ADMIN, organization
        )
        teacher = create_teacher_with_profile("teach10@test.com", organization)

        school_class = create_school_class(name="JSS1J", organization=organization)
        subject = create_subject(name="Government", code="GOV101", organization=organization)
        class_subject = create_class_subject(school_class, subject, teacher, organization=organization)

        timetable = create_timetable(class_subject, day="WEDNESDAY", start=time(11), end=time(12), organization=organization)

        login(api_client, admin.email, "testpass123", organization.id)

        resp = api_client.delete(f"/api/academics/timetables/{timetable.id}/")
        assert resp.status_code == 204
        # Double-check it's gone
        get_resp = api_client.get(f"/api/academics/timetables/{timetable.id}/")
        assert get_resp.status_code == 404

    def test_teacher_cannot_delete_timetable(self, api_client, organization):
        """Teachers should not be able to delete timetables."""
        teacher = create_teacher_with_profile("teach11@test.com", organization)

        school_class = create_school_class(name="JSS1K", organization=organization)
        subject = create_subject(name="Computer Science", code="CSC101", organization=organization)
        class_subject = create_class_subject(school_class, subject, teacher, organization=organization)

        timetable = create_timetable(class_subject, day="THURSDAY", start=time(9), end=time(10), organization=organization)

        login(api_client, teacher.membership.user.email, "testpass123", organization.id)

        resp = api_client.delete(f"/api/academics/timetables/{timetable.id}/")
        assert resp.status_code == 403
        assert "permission" in str(resp.json()).lower()

    def test_admin_can_update_only_room(self, api_client, organization):
        """Admin should be able to update only the room field."""
        admin = create_user_with_role("patchroom@test.com", Membership.RoleChoices.ADMIN, organization)
        teacher = create_teacher_with_profile("patchteacher@test.com", organization)
        school_class = create_school_class(name="JSS1I", organization=organization)
        subject = create_subject(name="Biology", code="BIO101", organization=organization)
        class_subject = create_class_subject(school_class, subject, teacher, organization=organization)

        login(api_client, admin.email, "testpass123", organization.id)

        timetable = create_timetable(class_subject, "MONDAY", time(10), time(11), "Room A", organization)

        resp = api_client.patch(f"/api/academics/timetables/{timetable.id}/", {
            "room": "Room B"
        }, format="json")

        assert resp.status_code == 200
        assert resp.json()["room"] == "Room B"

    def test_admin_can_update_only_start_time(self, api_client, organization):
        """Admin should be able to update only start_time."""
        admin = create_user_with_role("patchstart@test.com", Membership.RoleChoices.ADMIN, organization)
        teacher = create_teacher_with_profile("patchteacher2@test.com", organization)
        school_class = create_school_class(name="JSS1J", organization=organization)
        subject = create_subject(name="Geography", code="GEO101", organization=organization)
        class_subject = create_class_subject(school_class, subject, teacher, organization=organization)

        login(api_client, admin.email, "testpass123", organization.id)

        timetable = create_timetable(class_subject, "TUESDAY", time(9), time(10), "Room X", organization)

        resp = api_client.patch(f"/api/academics/timetables/{timetable.id}/", {
            "start_time": "08:30"
        }, format="json")

        assert resp.status_code == 200
        assert resp.json()["start_time"] == "08:30:00"

    def test_admin_can_update_only_day_of_week(self, api_client, organization):
        """Admin should be able to update only day_of_week."""
        admin = create_user_with_role("patchday@test.com", Membership.RoleChoices.ADMIN, organization)
        teacher = create_teacher_with_profile("patchteacher3@test.com", organization)
        school_class = create_school_class(name="JSS1K", organization=organization)
        subject = create_subject(name="Civic", code="CIV101", organization=organization)
        class_subject = create_class_subject(school_class, subject, teacher, organization=organization)

        login(api_client, admin.email, "testpass123", organization.id)

        timetable = create_timetable(class_subject, "WEDNESDAY", time(13), time(14), "Room Y", organization)

        resp = api_client.patch(f"/api/academics/timetables/{timetable.id}/", {
            "day_of_week": "FRIDAY"
        }, format="json")

        assert resp.status_code == 200
        assert resp.json()["day_of_week"] == "FRIDAY"

    def test_admin_cannot_patch_invalid_times(self, api_client, organization):
        """Admin should not be able to patch start_time/end_time into invalid range."""
        admin = create_user_with_role("patchinvalid@test.com", Membership.RoleChoices.ADMIN, organization)
        teacher = create_teacher_with_profile("patchteacher4@test.com", organization)
        school_class = create_school_class(name="JSS1L", organization=organization)
        subject = create_subject(name="Literature", code="LIT101", organization=organization)
        class_subject = create_class_subject(school_class, subject, teacher, organization=organization)

        login(api_client, admin.email, "testpass123", organization.id)

        timetable = create_timetable(class_subject, "FRIDAY", time(11), time(12), "Room Z", organization)

        resp = api_client.patch(f"/api/academics/timetables/{timetable.id}/", {
            "start_time": "13:00",
            "end_time": "12:00"
        }, format="json")

        assert resp.status_code == 400
        assert "Start time must be before end time." in str(resp.json())