import pytest
from attendance.serializers import AttendanceSessionSerializer, AttendanceRecordSerializer
from attendance.models import AttendanceSession, AttendanceRecord


@pytest.mark.django_db
def test_session_serializer_rejects_student_outside_class(api_rf, org, school_class, teacher, term, student_other_class):
    request = api_rf.post("/")
    request.user = teacher.user
    serializer = AttendanceSessionSerializer(
        data={
            "class_ref": school_class.id,
            "date": "2025-05-05",
            "period": "MORNING",
            "form_teacher": teacher.id,
            "records": [
                {"student": student_other_class.id, "status": "PRESENT"}
            ]
        },
        context={"request": request}
    )
    assert not serializer.is_valid()
    assert "student" in serializer.errors["records"][0]


@pytest.mark.django_db
def test_record_serializer_autofills_org_and_user(api_rf, org, session, student, teacher):
    request = api_rf.post("/")
    request.user = teacher.user
    serializer = AttendanceRecordSerializer(
        data={"student": student.id, "status": "ABSENT"},
        context={"request": request}
    )
    assert serializer.is_valid(), serializer.errors
    record = serializer.save(session=session)
    assert record.organization == org
    assert record.marked_by == teacher.user
