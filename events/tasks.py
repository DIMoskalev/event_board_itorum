from celery import shared_task
from django.utils import timezone

from events.models import Event


@shared_task
def update_event_status():
    threshold = timezone.now() - timezone.timedelta(hours=2)
    Event.objects.filter(status="upcoming", start_time__lte=threshold).update(
        status="finished"
    )
