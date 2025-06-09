import pytest
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from events.models import Event
from users.models import User

pytestmark = pytest.mark.django_db


class TestEventAPI:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='test', password='test')
        self.organizer = User.objects.create_user(username='test2', password='test2')
        self.event = Event.objects.create(
            title="Тестовое мероприятие",
            description="Тестовое описание",
            start_time=timezone.now() + timezone.timedelta(days=1),
            location="Москва",
            seats=2,
            status="upcoming",
            organizer=self.user,
        )

    def test_event_detail(self):
        response = self.client.get(f"/api/events/{self.event.id}/")
        assert response.status_code == 200
        assert response.data["id"] == 1
        assert response.data["organizer"]["username"] == "test"
        assert response.data["title"] == "Тестовое мероприятие"
        assert response.data["location"] == "Москва"

    def test_create_event_unauthorized(self):
        response = self.client.post("/api/events/", {
            "title": "Незарегистрированное мероприятие",
            "description": "Не нужно",
            "start_time": timezone.now() + timezone.timedelta(days=1),
            "location": "Город",
            "seats": 100,
            "status": "upcoming",
        })
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_event_by_organizer(self):
        self.client.force_authenticate(user=self.organizer)
        response = self.client.post("/api/events/", {
            "title": "Новое мероприятие",
            "description": "Еще одно событие",
            "start_time": timezone.now() + timezone.timedelta(days=1),
            "location": "Питер",
            "seats": 50,
            "status": "upcoming",
        })
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["title"] == "Новое мероприятие"

    def test_list_events(self):
        self.client.force_authenticate(user=self.organizer)
        self.client.post("/api/events/", {
            "title": "Новое мероприятие",
            "description": "Еще одно событие",
            "start_time": timezone.now() + timezone.timedelta(days=1),
            "location": "Питер",
            "seats": 50,
            "status": "upcoming",
        })
        response = self.client.get("/api/events/")
        assert response.status_code == 200
        print(response.data)
        assert len(response.data) > 1

    def test_update_event_by_non_organizer(self):
        self.client.force_authenticate(user=self.organizer)
        response = self.client.patch(f"/api/events/{self.event.id}/", {
            "title": "Тестовое мероприятие"
        })
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_event_by_organizer(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(f"/api/events/{self.event.id}/", {
            "title": "Обновленное тестовое мероприятие"
        })
        assert response.status_code == status.HTTP_200_OK
        assert response.data["title"] == "Обновленное тестовое мероприятие"

    def test_delete_event_within_hour(self):
        self.event.created_at = timezone.now() - timezone.timedelta(minutes=5)
        self.event.save()
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(f"/api/events/{self.event.id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_delete_event_after_hour(self):
        self.event.created_at = timezone.now() + timezone.timedelta(hours=2)
        self.event.save()
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(f"/api/events/{self.event.id}/")
        assert response.data == {"error": "Удаление возможно только в течение 1 часа после создания"}
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_book_event(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(f"/api/events/{self.event.id}/book/")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["booking_id"] == 1

    def test_book_non_existent_event(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(f"/api/events/{self.event.id + 1}/book/")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data == {"error": "Мероприятие не найдено"}

    def test_book_event_unauthorized_user(self):
        response = self.client.post(f"/api/events/{self.event.id}/book/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_book_event_again(self):
        self.client.force_authenticate(user=self.user)
        self.client.post(f"/api/events/{self.event.id}/book/")
        response = self.client.post(f"/api/events/{self.event.id}/book/")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["error"] == "Вы уже зарегистрированы"

    def test_cancel_booking_event(self):
        self.client.force_authenticate(user=self.user)
        self.client.post(f"/api/events/{self.event.id}/book/")
        response = self.client.post(f"/api/events/{self.event.id}/cancel_booking/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data == {"status": "Бронь отменена"}

    def test_cancel_unbooking_event(self):
        self.client.force_authenticate(user=self.user)
        self.client.post(f"/api/events/{self.event.id}/book/")
        self.client.post(f"/api/events/{self.event.id}/cancel_booking/")
        response = self.client.post(f"/api/events/{self.event.id}/cancel_booking/")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == {"error": "Вы не были зарегистрированы"}

    def test_cancel_non_existent_event(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(f"/api/events/{self.event.id + 1}/cancel_booking/")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data == {"error": "Мероприятие не найдено"}

    def test_book_no_free_seats_event(self):
        self.client.force_authenticate(user=self.user)
        self.event.seats = 0
        self.event.save()
        response = self.client.post(f"/api/events/{self.event.id}/book/")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == {"error": "Нет свободных мест"}

    def test_book_finished_event(self):
        self.client.force_authenticate(user=self.user)
        self.event.status = "finished"
        self.event.save()
        response = self.client.post(f"/api/events/{self.event.id}/book/")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == {"error": "Нельзя бронировать прошедшие/отменённые мероприятия"}

    def test_rate_upcoming_event(self):
        self.client.force_authenticate(user=self.user)
        self.client.post(f"/api/events/{self.event.id}/book/")
        response = self.client.post(f"/api/events/{self.event.id}/rate/", {"rating": 5})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == {"error": "Оценку можно оставить только после мероприятия"}

    def test_rate_event_without_booking(self):
        self.client.force_authenticate(user=self.user)
        self.event.start_time = self.event.start_time - timezone.timedelta(days=2)
        self.event.status = "finished"
        self.event.save()
        response = self.client.post(f"/api/events/{self.event.id}/rate/", {"rating": 5})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == {"error": "Вы не участвовали в мероприятии"}

    def test_rate_finished_booked_event(self):
        self.client.force_authenticate(user=self.user)
        self.client.post(f"/api/events/{self.event.id}/book/")
        self.event.start_time = self.event.start_time - timezone.timedelta(days=2)
        self.event.status = "finished"
        self.event.save()
        response = self.client.post(f"/api/events/{self.event.id}/rate/", {"score": 5})
        print(response.data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["score"] == 5


    def test_fail_rate_finished_booked_event(self):
        self.client.force_authenticate(user=self.user)
        self.client.post(f"/api/events/{self.event.id}/book/")
        self.event.start_time = self.event.start_time - timezone.timedelta(days=2)
        self.event.status = "finished"
        self.event.save()
        response = self.client.post(f"/api/events/{self.event.id}/rate/", {"score": 6})
        print(response.data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == {"error": "Оцените событие от 1 до 5 "}

