import pytest
from datetime import date, timedelta
from attendance.services import compute_weekly_summary_for_student, compute_term_summary_for_student
from attendance.models import WeeklyAttendanceSummary, TermAttendanceSummary


@pytest.mark.django_db
def test_compute_weekly_summary(student, school_class, org, session_present):
    week_start = date.today() - timedelta(days=date.today().weekday())
    week_end = week_start + timedelta(days=4)

    compute_weekly_summary_for_student(student, school_class, week_start, week_end, org)
    summary = WeeklyAttendanceSummary.objects.get(student=student)
    assert summary.total_sessions >= 1
    assert summary.attended_sessions <= summary.total_sessions


@pytest.mark.django_db
def test_compute_term_summary(student, school_class, org, term, session_present):
    compute_term_summary_for_student(student, school_class, term, org)
    summary = TermAttendanceSummary.objects.get(student=student, term=term)
    assert summary.total_sessions >= 1
