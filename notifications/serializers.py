from rest_framework import serializers

from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    type_display = serializers.SerializerMethodField()

    def get_type_display(self, obj):
        return obj.get_type_display()

    class Meta:
        model = Notification
        exclude = ("type",)
