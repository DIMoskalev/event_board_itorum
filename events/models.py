from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from users.models import User


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Тэг"
        verbose_name_plural = "Тэги"


class Event(models.Model):
    STATUS_CHOICES = [
        ("upcoming", "Ожидается"),
        ("cancelled", "Отменено"),
        ("finished", "Завершено"),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField()
    start_time = models.DateTimeField()
    location = models.CharField(max_length=255)
    seats = models.PositiveIntegerField(default=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="upcoming")
    organizer = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="created_events"
    )
    tags = models.ManyToManyField(Tag, related_name="events", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    @property
    def free_seats(self):
        return self.seats - self.bookings.count()

    def average_rating(self):
        average_rating = self.ratings.aggregate(models.Avg("score"))["score__avg"]
        if average_rating is None:
            return 0.0
        return average_rating

    class Meta:
        ordering = ["start_time"]
        verbose_name = "Событие"
        verbose_name_plural = "События"


class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="bookings")
    booked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "event")
        verbose_name = "Бронирование"
        verbose_name_plural = "Бронирования"


class Rating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="ratings")
    score = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    rated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "event")
        verbose_name = "Оценка"
        verbose_name_plural = "Оценки"
