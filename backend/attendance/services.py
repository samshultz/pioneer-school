from datetime import timedelta
from django.conf import settings
from django.utils.timezone import localdate
from django.db.models import Count, Sum

from .models import (
    AttendanceRecord, 
    WeeklyAttendanceSummary, 
    TermAttendanceSummary,
    WeeklyClassAttendanceSummary,
    TermClassAttendanceSummary
)
from academics.models import Term

def get_week_bounds(date):
    """Return start (Monday) and end (Friday) of the week for a given date."""
    start = date - timedelta(days=date.weekday())  # Monday
    end = start + timedelta(days=4)  # Friday (ignoring weekends)
    return start, end

def compute_weekly_summary_for_student(student, class_ref, week_start, week_end, organization):
    """Compute/update weekly summary for a student."""

    records = AttendanceRecord.objects.filter(
        student=student,
        session__class_ref=class_ref,
        session__date__range=(week_start, week_end),
        organization=organization,
        session__date__range=[week_start, week_end],
    )

    total_sessions = records.count()
    attended_sessions = records.filter(status="PRESENT").count()
    percentage = (attended_sessions / total_sessions * 100) if total_sessions else 0

    WeeklyAttendanceSummary.objects.update_or_create(
        organization=organization,
        class_ref=class_ref,
        student=student,
        week_start=week_start,
        week_end=week_end,
        total_sessions=total_sessions,
        attended_sessions=attended_sessions,
        percentage=percentage,
        # defaults={
        #     "total_sessions": total_sessions,
        #     "attended_sessions": attended_sessions,
        #     "percentage": percentage,
        # }
    )


def compute_term_summary_for_student(student, class_ref, term, organization):
    """Compute/update term summary for a student."""
    records = AttendanceRecord.objects.filter(
        organization=organization,
        student=student,
        session__class_ref=class_ref,
        session__date__range=(term.start_date, term.end_date),
    )

    total_sessions = records.count()
    attended_sessions = records.filter(status="PRESENT").count()
    percentage = (attended_sessions / total_sessions * 100) if total_sessions else 0

    TermAttendanceSummary.objects.update_or_create(
        organization=organization,
        class_ref=class_ref,
        student=student,
        term=term,
        total_sessions=total_sessions,
        attended_sessions=attended_sessions,
        percentage=percentage
        # defaults={
        #     "total_sessions": total_sessions,
        #     "attended_sessions": attended_sessions,
        #     "percentage": percentage,
        # }
    )

def compute_weekly_summaries(class_ref, week_start, week_end, organization):
    """Compute per-student and class-level attendance summaries for a given week."""

    # --- Per Student Summaries (already had this logic) ---
    students = class_ref.students.all()
    for student in students:
        records = AttendanceRecord.objects.filter(
            organization=organization,
            student=student,
            session__class_ref=class_ref,
            session__date__gte=week_start,
            session__date__lte=week_end,
        )

        total_sessions = records.count()
        attended_sessions = records.filter(status="PRESENT").count()

        percentage = (attended_sessions / total_sessions) * 100 if total_sessions else 0

        WeeklyAttendanceSummary.objects.update_or_create(
            organization=organization,
            class_ref=class_ref,
            student=student,
            week_start=week_start,
            week_end=week_end,
            total_sessions=total_sessions,
            attended_sessions=attended_sessions,
            percentage=percentage
            # defaults={
            #     "total_sessions": total_sessions,
            #     "attended_sessions": attended_sessions,
            #     "percentage": percentage,
            # },
        )

    # --- Class-level Summary ---
    class_records = AttendanceRecord.objects.filter(
        organization=organization,
        student__school_class=class_ref,
        session__date__gte=week_start,
        session__date__lte=week_end,
    )

    total_sessions = class_records.count()
    attended_sessions = class_records.filter(status="PRESENT").count()
    percentage = (attended_sessions / total_sessions) * 100 if total_sessions else 0

    WeeklyClassAttendanceSummary.objects.update_or_create(
        organization=organization,
        class_ref=class_ref,
        week_start=week_start,
        week_end=week_end,
        defaults={
            "total_sessions": total_sessions,
            "attended_sessions": attended_sessions,
            "percentage": percentage,
        },
    )

def update_weekly_class_summary(class_ref, week_start, week_end, organization):
    """Compute/update class-level weekly summary."""
    records = AttendanceRecord.objects.filter(
        organization=organization,
        session__class_ref=class_ref,
        session__date__range=(week_start, week_end),
    )

    total_sessions = records.count()
    attended_sessions = records.filter(status=AttendanceRecord.Status.PRESENT).count()
    percentage = (attended_sessions / total_sessions * 100) if total_sessions else 0

    WeeklyClassAttendanceSummary.objects.update_or_create(
        organization=organization,
        class_ref=class_ref,
        week_start=week_start,
        week_end=week_end,
        defaults={
            "total_sessions": total_sessions,
            "attended_sessions": attended_sessions,
            "percentage": percentage,
        }
    )


def update_term_class_summary(class_ref, term, organization):
    """Compute/update class-level term summary."""
    records = AttendanceRecord.objects.filter(
        organization=organization,
        session__class_ref=class_ref,
        session__date__range=(term.start_date, term.end_date),
    ).select_related("student")

    total_sessions = records.count()
    attended_sessions = records.filter(status=AttendanceRecord.Status.PRESENT).count()

    male_attendance = records.filter(student__gender="MALE", status=AttendanceRecord.Status.PRESENT).count()
    female_attendance = records.filter(student__gender="FEMALE", status=AttendanceRecord.Status.PRESENT).count()

    avg_percentage = (attended_sessions / total_sessions * 100) if total_sessions else 0

    TermClassAttendanceSummary.objects.update_or_create(
        organization=organization,
        class_ref=class_ref,
        term=term,
        defaults={
            "total_sessions": total_sessions,
            "attended_sessions": attended_sessions,
            "male_attendance": male_attendance,
            "female_attendance": female_attendance,
            "average_percentage": avg_percentage,
        }
    )

def compute_term_summary_for_student(student, class_ref, term, organization):
    """Compute/update term summary for a student."""
    records = AttendanceRecord.objects.filter(
        organization=organization,
        student=student,
        session__class_ref=class_ref,
        session__date__range=(term.start_date, term.end_date),
    )

    total_sessions = records.count()
    attended_sessions = records.filter(status=AttendanceRecord.Status.PRESENT).count()
    percentage = (attended_sessions / total_sessions * 100) if total_sessions else 0

    TermAttendanceSummary.objects.update_or_create(
        organization=organization,
        class_ref=class_ref,
        student=student,
        term=term,
        total_sessions=total_sessions,
        attended_sessions=attended_sessions,
        percentage=percentage
        # defaults={
        #     "total_sessions": total_sessions,
        #     "attended_sessions": attended_sessions,
        #     "percentage": percentage,
        # }
    )

def recompute_all_summaries(attendance_record):
    """
    Recompute weekly + term summaries for both student and class
    based on a given AttendanceRecord.
    """
    session = attendance_record.session
    org = session.organization
    student = attendance_record.student
    class_ref = session.class_ref
    date = session.date

    # --- Weekly range (Mon–Fri) ---
    week_start = date - timedelta(days=date.weekday())
    week_end = week_start + timedelta(days=4)

    # Student weekly summary
    compute_weekly_summary_for_student(student, class_ref, week_start, week_end, org)

    # Class weekly summary
    update_weekly_class_summary(class_ref, week_start, week_end, org)

    # --- Term summaries ---
    try:
        term = Term.objects.get(
            organization=org,
            start_date__lte=date,
            end_date__gte=date
        )

        # Student term summary
        compute_term_summary_for_student(student, class_ref, term, org)

        # Class term summary
        update_term_class_summary(class_ref, term, org)

    except Term.DoesNotExist:
        # No active term found for this record
        pass

def schedule_recompute_summaries(record_id):
    """
    Schedule recompute depending on settings:
    - Sync if ATTENDANCE_ASYNC_UPDATES = False
    - Async via Celery if ATTENDANCE_ASYNC_UPDATES = True
    """
    if getattr(settings, "ATTENDANCE_ASYNC_UPDATES", False):
        from .tasks import recompute_summaries_task
        recompute_summaries_task.delay(record_id)
    else:
        try:
            record = AttendanceRecord.objects.get(pk=record_id)
        except AttendanceRecord.DoesNotExist:
            return
        recompute_all_summaries(record)