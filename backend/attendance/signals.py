from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import AttendanceRecord
from .services import schedule_recompute_summaries


@receiver(post_save, sender=AttendanceRecord)
def attendance_record_saved(sender, instance, **kwargs):
    """When an AttendanceRecord is created/updated, recompute summaries."""
    schedule_recompute_summaries(instance.id)


@receiver(post_delete, sender=AttendanceRecord)
def attendance_record_deleted(sender, instance, **kwargs):
    """When an AttendanceRecord is deleted, recompute summaries."""
    schedule_recompute_summaries(instance.id)