from django.db import IntegrityError, transaction
from django.db.models import Avg, Case, DateTimeField, F, IntegerField, Q, Value, When
from django.db.models.functions import Coalesce
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from notifications.tasks import send_notification

from .filters import EventFilter
from .models import Booking, Event, Rating, Tag
from .permissions import IsOrganizerOrReadOnly
from .serializers import (
    BookingSerializer,
    EventCreateSerializer,
    EventDetailSerializer,
    EventListSerializer,
    RatingSerializer,
    TagCreateSerializer,
    TagSerializer,
)


class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all().prefetch_related("tags", "organizer", "ratings")
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOrganizerOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = EventFilter
    search_fields = ["title", "description", "tags__name"]

    def get_serializer_class(self):
        if self.action == "list":
            return EventListSerializer
        elif self.action == "retrieve":
            return EventDetailSerializer
        elif self.action in ["create", "update", "partial_update"]:
            return EventCreateSerializer
        return EventListSerializer

    def perform_create(self, serializer):
        serializer.save(organizer=self.request.user)

    def get_permissions(self):
        if self.action in ["update", "partial_update", "destroy"]:
            return [permissions.IsAuthenticated(), IsOrganizerOrReadOnly()]
        return [permissions.IsAuthenticatedOrReadOnly()]

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = self.filter_queryset(queryset)
        queryset = queryset.annotate(
            avg_rating=Coalesce(Avg("ratings__score"), Value(0.0)),
            status_order=Case(
                When(status="upcoming", then=Value(0)),
                default=Value(1),
                output_field=IntegerField(),
            ),
            start_time_asc=Case(
                When(status="upcoming", then=F("start_time")),
                default=Value(None),
                output_field=DateTimeField(),
            ),
            start_time_desc=Case(
                When(~Q(status="upcoming"), then=F("start_time")),
                default=Value(None),
                output_field=DateTimeField(),
            ),
        ).order_by(
            "status_order",
            "start_time_asc",
            "-start_time_desc",
            "-avg_rating",
        )

        return queryset

    @action(
        detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated]
    )
    def book(self, request, pk=None):
        try:
            with transaction.atomic():
                event = Event.objects.select_for_update().get(id=pk)

                if event.status != "upcoming":
                    return Response(
                        {"error": "Нельзя бронировать прошедшие/отменённые мероприятия"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                if event.free_seats <= 0:
                    return Response(
                        {"error": "Нет свободных мест"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                booking, created = Booking.objects.get_or_create(
                    user=request.user, event=event
                )
                if not created:
                    return Response(
                        {"error": "Вы уже зарегистрированы"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                send_notification.delay(
                    request.user.id,
                    event.id,
                    "booking",
                    f'Вы успешно забронировали мероприятие "{event.title}"',
                )
                serializer = BookingSerializer(booking)

                return Response(
                    {
                        "booking_id": serializer.data["id"],
                        "booked_at": serializer.data["booked_at"],
                        "message": serializer.data["message"],
                    },
                    status=status.HTTP_201_CREATED,
                )

        except Event.DoesNotExist:
            return Response(
                {"error": "Мероприятие не найдено"}, status=status.HTTP_404_NOT_FOUND
            )
        except IntegrityError:
            return Response(
                {"error": "Ошибка при создании бронирования"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            print(e)
            return Response(
                {"error": "Ошибка при обработке запроса"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(
        detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated]
    )
    def cancel_booking(self, request, pk=None):
        try:
            with transaction.atomic():
                event = Event.objects.select_for_update().get(id=pk)

                try:
                    booking = Booking.objects.get(user=request.user, event=event)
                except Booking.DoesNotExist:
                    return Response(
                        {"error": "Вы не были зарегистрированы"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                booking.delete()

                send_notification.delay(
                    request.user.id,
                    event.id,
                    "cancel",
                    f'Вы отменили бронирование мероприятия "{event.title}"',
                )

                return Response({"status": "Бронь отменена"},
                                status=status.HTTP_200_OK)

        except Event.DoesNotExist:
            return Response(
                {"error": "Мероприятие не найдено"}, status=status.HTTP_404_NOT_FOUND
            )
        except IntegrityError:
            return Response(
                {"error": "Ошибка при отмене брони"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception:
            return Response(
                {"error": "Ошибка при обработке запроса"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(
        detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated]
    )
    def my_upcoming_events(self, request):
        events = self.queryset.filter(
            bookings__user=request.user,
            start_time__gte=timezone.now(),
            status="upcoming",
        ).distinct()
        # serializer = EventListSerializer(events, many=True)
        serializer = self.get_serializer(events, many=True)
        return Response(serializer.data)

    @action(
        detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated]
    )
    def rate(self, request, pk=None):
        event = self.get_object()
        if event.start_time > timezone.now():
            return Response(
                {"error": "Оценку можно оставить только после мероприятия"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not Booking.objects.filter(user=request.user, event=event).exists():
            return Response(
                {"error": "Вы не участвовали в мероприятии"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        score = request.data.get("score")
        if not score or not (1 <= int(score) <= 5):
            return Response(
                {"error": "Оцените событие от 1 до 5 "},
                status=status.HTTP_400_BAD_REQUEST,
            )

        rating, _ = Rating.objects.update_or_create(
            user=request.user, event=event, defaults={"score": score}
        )
        return Response(RatingSerializer(rating).data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if (timezone.now() - instance.created_at).seconds > 3600:
            return Response(
                {"error": "Удаление возможно только в течение 1 часа после создания"},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().destroy(request, *args, **kwargs)


class TagViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, GenericViewSet):
    queryset = Tag.objects.all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        if self.action == "create":
            return TagCreateSerializer
        else:
            return TagSerializer
