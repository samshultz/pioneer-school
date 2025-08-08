import pytest
from attendance.models import WeeklyAttendanceSummary


@pytest.mark.django_db
def test_signal_recomputes_summary_on_record_save(session, student, org):
    from attendance.models import AttendanceRecord
    AttendanceRecord.objects.create(
        organization=org, 
        session=session, 
        student=student, 
        status="PRESENT"
    )
    # After save → summaries should exist
    assert WeeklyAttendanceSummary.objects.filter(
        student=student).exists()
