from django.db import models

from events.models import Event
from users.models import User


class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ("booking", "Забронировано"),
        ("cancel", "Бронирование отменено"),
        ("reminder", "Напоминание"),
    )

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notifications"
    )
    event = models.ForeignKey(
        Event,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="event_notifications",
    )
    type = models.CharField(max_length=10, choices=NOTIFICATION_TYPES)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.type} - {self.event.title}"

    class Meta:
        verbose_name = "Уведомление"
        verbose_name_plural = "Уведомления"
