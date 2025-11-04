from rest_framework import serializers
from .models import EmailNotification
from users.serializers import UserSerializer
from events.serializers import EventListSerializer


class EmailNotificationSerializer(serializers.ModelSerializer):
    """Serializer for EmailNotification model"""
    recipient = UserSerializer(read_only=True)
    event = EventListSerializer(read_only=True)

    class Meta:
        model = EmailNotification
        fields = (
            'id', 'recipient', 'event', 'notification_type', 'subject',
            'message', 'status', 'error_message', 'sent_at', 'created_at'
        )
        read_only_fields = ('id', 'created_at')
