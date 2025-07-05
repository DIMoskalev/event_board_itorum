import pytest
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from events.models import Event
from notifications.models import Notification
from users.models import User

@pytest.mark.django_db
class TestNotificationAPI:

    @pytest.fixture
    def user(self):
        return User.objects.create_user(username="test_user", password="password")

    @pytest.fixture
    def auth_client(self, user):
        client = APIClient()
        client.force_authenticate(user=user)
        return client

    @pytest.fixture
    def event(self, user):
        return Event.objects.create(
            title="Тестовое мероприятие",
            description="Тестовое описание",
            start_time=timezone.now() + timezone.timedelta(days=1),
            location="Москва",
            seats=2,
            status="upcoming",
            organizer=user,
        )

    @pytest.fixture
    def notification_booked(self, user, event):
        return Notification.objects.create(
            user=user,
            event=event,
            type="booking",
            message="Вы записались на событие",
        )

    @pytest.fixture
    def notification_canceled(self, user, event):
        return Notification.objects.create(
            user=user,
            event=event,
            type="cancel",
            message="Вы отменили бронь на событие",
        )

    def test_notification_detail_booked(self, auth_client, notification_booked):
        response = auth_client.get("/api/notifications/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 4
        print(response.data)
        assert response.data["results"][0]["message"] == "Вы записались на событие"

    def test_notification_list_without_auth(self):
        client = APIClient()
        response = client.get("/api/notifications/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_notification_type_display(self, auth_client, notification_booked):
        response = auth_client.get("/api/notifications/")
        assert response.status_code == 200
        print(response.data)
        assert response.data["results"][0]["type_display"] == "Забронировано"

    def test_notification_detail_canceled(self, auth_client, notification_canceled):
        response = auth_client.get("/api/notifications/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 4
        assert response.data["results"][0]["message"] == "Вы отменили бронь на событие"