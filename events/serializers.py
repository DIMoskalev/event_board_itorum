from rest_framework import serializers

from users.serializers import UserSerializer

from .models import Booking, Event, Rating, Tag


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ("id", "name")


class EventListSerializer(serializers.ModelSerializer):
    organizer = UserSerializer()
    tags = TagSerializer(many=True)
    free_seats = serializers.IntegerField(read_only=True)
    avg_rating = serializers.FloatField(read_only=True)
    status = serializers.SerializerMethodField()

    def get_status(self, obj):
        return obj.get_status_display()

    class Meta:
        model = Event
        fields = (
            "id",
            "title",
            "location",
            "start_time",
            "status",
            "organizer",
            "tags",
            "free_seats",
            "avg_rating",
        )


class EventDetailSerializer(serializers.ModelSerializer):
    organizer = UserSerializer()
    tags = TagSerializer(many=True)
    free_seats = serializers.IntegerField(read_only=True)
    avg_rating = serializers.FloatField(read_only=True)
    status = serializers.SerializerMethodField()

    def get_status(self, obj):
        return obj.get_status_display()

    class Meta:
        model = Event
        fields = "__all__"


class EventCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        exclude = ("organizer",)


class BookingSerializer(serializers.ModelSerializer):
    event = serializers.PrimaryKeyRelatedField(read_only=True)
    message = serializers.SerializerMethodField()

    def get_message(self, obj):
        event = obj.event
        return (
            f'Вы успешно забронировали место на событие "{event.title}" \n'
            f"Место проведения - {event.location}, Начало - {event.start_time.strftime('%d.%m.%Y %H:%M')}"
        )

    class Meta:
        model = Booking
        fields = ("id", "event", "booked_at", "message")


class RatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rating
        fields = ("id", "event", "score")


class TagCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ("name",)
