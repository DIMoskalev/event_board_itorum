from celery import shared_task
from django.utils import timezone

from events.models import Event
from users.models import User

from .models import Notification


@shared_task
def send_notification(user_id, event_id, notification_type, message):
    user = User.objects.get(id=user_id)
    event = None
    if event_id is not None:
        event = Event.objects.get(id=event_id)

    Notification.objects.create(
        user=user, event=event, type=notification_type, message=message
    )
    print(f"Уведомление пользователю {user_id}: {message}")


@shared_task
def send_reminder_notifications():
    now = timezone.now()
    one_hour_later = now + timezone.timedelta(hours=1)

    events = Event.objects.prefetch_related("bookings").filter(
        status="upcoming", start_time__range=(now, one_hour_later)
    )

    for event in events:
        bookings = event.bookings.all()
        for booking in bookings:
            send_notification.delay(
                booking.user.id,
                event.id,
                "reminder",
                f"Напоминание: мероприятие {event.title} начнется через час."
                f"Время начала мероприятия: {timezone.localtime(event.start_time).strftime('%H:%M')}.",
            )
