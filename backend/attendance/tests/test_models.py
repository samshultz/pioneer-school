import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date, timedelta
from attendance.models import AttendanceSession, AttendanceRecord, Holiday
from academics.models import Class, Term
from users.models import Organization, TeacherProfile, StudentProfile, User


@pytest.mark.django_db
def test_cannot_create_duplicate_session(org, school_class, teacher, term):
    AttendanceSession.objects.create(
        organization=org,
        class_ref=school_class,
        date=date.today(),
        period="MORNING",
        term=term,
        form_teacher=teacher
    )
    with pytest.raises(Exception):
        AttendanceSession.objects.create(
            organization=org,
            class_ref=school_class,
            date=date.today(),
            period="MORNING",
            term=term,
            form_teacher=teacher
        )


@pytest.mark.django_db
def test_cannot_mark_student_not_in_class(org, school_class, teacher, term, student_other_class):
    session = AttendanceSession.objects.create(
        organization=org, class_ref=school_class, date=date.today(),
        period="MORNING", term=term, form_teacher=teacher
    )
    record = AttendanceRecord(
        organization=org, session=session, student=student_other_class, status="PRESENT"
    )
    with pytest.raises(ValidationError):
        record.full_clean()


@pytest.mark.django_db
def test_holiday_unique_per_org(org):
    Holiday.objects.create(organization=org, date=date.today(), description="Xmas")
    with pytest.raises(Exception):
        Holiday.objects.create(organization=org, date=date.today(), description="Duplicate")
