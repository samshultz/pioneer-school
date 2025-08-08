import pytest
from rest_framework.test import APIClient
from django.urls import reverse
from datetime import date


@pytest.mark.django_db
def test_teacher_can_create_session(org, school_class, teacher, term):
    client = APIClient()
    client.force_authenticate(user=teacher.membership.user)
    url = reverse("attendance-session-list")
    resp = client.post(url, {
        "class_ref": school_class.id,
        "date": str(date.today()),
        "period": "MORNING",
        "form_teacher": teacher.id,
        "term": term.id
    }, format="json")
    assert resp.status_code == 201


@pytest.mark.django_db
def test_student_cannot_create_session(api_client_student, school_class, session):
    url = reverse("attendance-session-list")
    resp = api_client_student.post(url, {
        "class_ref": school_class.id,
        "date": str(date.today()),
        "period": "MORNING",
        "form_teacher": session.form_teacher.id
    }, format="json")
    assert resp.status_code == 403


@pytest.mark.django_db
def test_bulk_record_creation(api_client_teacher, session, students):
    url = reverse("attendance-session-records", args=[session.id])
    data = [{"student": s.id, "status": "PRESENT"} for s in students]
    resp = api_client_teacher.post(url, data, format="json")
    assert resp.status_code == 201
    assert len(resp.json()) == len(students)
