from django.contrib import admin
from django.db.models import Avg, Count, ExpressionWrapper, F, IntegerField

from events.models import Booking, Event, Rating, Tag


class FreeSeatsFilter(admin.SimpleListFilter):
    title = "Наличие свободных мест"
    parameter_name = "free_seats"

    def lookups(self, request, model_admin):
        return [
            ("yes", "Есть свободные места"),
            ("no", "Нет свободных мест"),
        ]

    def queryset(self, request, queryset):
        queryset = queryset.annotate(
            booked_seats=Count("bookings"),
            free_seats_calc=ExpressionWrapper(
                F("seats") - Count("bookings"), output_field=IntegerField()
            ),
        )
        if self.value() == "yes":
            return queryset.filter(free_seats_calc__gt=0)
        elif self.value() == "no":
            return queryset.filter(free_seats_calc__lte=0)
        return queryset


class AvgRatingFilter(admin.SimpleListFilter):
    title = "Средний рейтинг"
    parameter_name = "avg_rating"

    def lookups(self, request, model_admin):
        return [
            ("<3.0", "Меньше 3"),
            ("3.0-4.0", "От 3 до 4"),
            ("4+", "Больше 4"),
        ]

    def queryset(self, request, queryset):
        queryset = queryset.annotate(avg_rating=Avg("ratings__score"))
        value = self.value()
        if value == "<3":
            return queryset.filter(avg_rating__lt=3.0)
        if value == "3.0-4.0":
            return queryset.filter(avg_rating__gte=3.0, avg_rating__lt=4.0)
        if value == "4+":
            return queryset.filter(avg_rating__gte=4.0)
        return queryset


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "start_time",
        "location",
        "seats",
        "free_seats",
        "status",
        "average_rating",
    )
    list_filter = (
        "status",
        "start_time",
        "organizer",
        "location",
        AvgRatingFilter,
        FreeSeatsFilter,
    )
    search_fields = ("title", "description")


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "event",
        "booked_at",
    )
    list_filter = (
        "user",
        "event",
        "booked_at",
    )
    search_fields = (
        "user",
        "event",
    )


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "event",
        "score",
    )
    list_filter = (
        "user",
        "event",
        "score",
    )
    search_fields = (
        "user",
        "event",
    )


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name",)
    list_filter = ("name",)
    search_fields = ("name",)
