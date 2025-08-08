from django.core.management.base import BaseCommand
from attendance.services import update_weekly_class_summary, update_term_class_summary
from academics.models import Term, Class
from attendance.models import AttendanceRecord
from datetime import timedelta

class Command(BaseCommand):
    help = "Recompute all weekly and term attendance summaries"

    def handle(self, *args, **options):
        for cls in Class.objects.all():
            org = cls.organization
            # weekly summaries
            first_record = AttendanceRecord.objects.filter(session__class_ref=cls).order_by("session__date").first()
            last_record = AttendanceRecord.objects.filter(session__class_ref=cls).order_by("-session__date").first()

            if not first_record:
                continue

            start_date = first_record.session.date
            end_date = last_record.session.date

            current = start_date - timedelta(days=start_date.weekday())
            while current <= end_date:
                week_start = current
                week_end = current + timedelta(days=4)
                update_weekly_class_summary(cls, week_start, week_end, org)
                current += timedelta(weeks=1)

            # term summaries
            for term in Term.objects.filter(organization=org):
                update_term_class_summary(cls, term, org)

        self.stdout.write(self.style.SUCCESS("Attendance summaries recomputed successfully"))