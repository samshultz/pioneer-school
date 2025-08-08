from celery import shared_task
from .models import AttendanceRecord
from .services import recompute_all_summaries

@shared_task
def recompute_summaries_task(record_id):
    """
    Celery task to recompute summaries for an AttendanceRecord.
    """
    try:
        record = AttendanceRecord.objects.get(pk=record_id)
    except AttendanceRecord.DoesNotExist:
        return recompute_all_summaries(record)