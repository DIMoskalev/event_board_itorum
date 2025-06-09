from django.contrib import admin

from notifications.models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "event", "type", "created_at", "message")
    list_filter = ("user", "type")
    search_fields = ("user__username", "event__title")
