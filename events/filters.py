import django_filters

from .models import Event


class EventFilter(django_filters.FilterSet):
    location = django_filters.CharFilter(field_name="location", lookup_expr="iexact")
    status = django_filters.CharFilter(field_name="status", lookup_expr="iexact")
    start_time = django_filters.DateFilter(field_name="start_time", lookup_expr="date")
    tag = django_filters.CharFilter(field_name="tags__name", lookup_expr="icontains")
    free_seats = django_filters.BooleanFilter(method="filter_free_seats")

    avg_rating__gte = django_filters.NumberFilter(
        field_name="average_rating", lookup_expr="gte"
    )
    avg_rating__lte = django_filters.NumberFilter(
        field_name="average_rating", lookup_expr="lte"
    )

    class Meta:
        model = Event
        fields = [
            "location",
            "status",
            "start_time",
            "tag",
            "free_seats",
            "avg_rating__gte",
            "avg_rating__lte",
        ]

    def filter_free_seats(self, queryset, name, value):
        if value:
            return queryset.filter(bookings__isnull=False).distinct()
        return queryset
