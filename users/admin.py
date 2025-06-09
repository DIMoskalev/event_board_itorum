from django.contrib import admin

from users.models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        "email",
        "first_name",
        "last_name",
        "is_active",
        "is_staff",
    )
    list_filter = (
        "email",
        "first_name",
    )
    search_fields = (
        "email",
        "first_name",
        "last_name",
    )
