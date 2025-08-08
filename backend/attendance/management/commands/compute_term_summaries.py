from django.core.management.base import BaseCommand
from academics.models import Term
from attendance.services import compute_term_summary_for_student
from users.models import StudentProfile


class Command(BaseCommand):
    help = "Compute term attendance summaries for all students"

    def add_arguments(self, parser):
        parser.add_argument("term_id", type=int, help="ID of the term")

    def handle(self, *args, **options):
        term_id = options["term_id"]
        try:
            term = Term.objects.get(id=term_id)
        except Term.DoesNotExist:
            self.stderr.write(f"❌ Term {term_id} does not exist")
            return

        for student in StudentProfile.objects.filter(organization=term.organization):
            class_ref = student.school_class
            compute_term_summary_for_student(student, class_ref, term, term.organization)

        self.stdout.write(self.style.SUCCESS(f"✅ Term summaries computed for term {term_id}"))