from rest_framework import serializers
from .models import Review
from users.serializers import UserSerializer
from events.serializers import EventListSerializer


class ReviewSerializer(serializers.ModelSerializer):
    """Serializer for Review model"""
    user = UserSerializer(read_only=True)
    event = EventListSerializer(read_only=True)

    class Meta:
        model = Review
        fields = (
            'id', 'event', 'user', 'rating', 'title', 'content',
            'is_moderated', 'is_approved', 'created_at', 'updated_at'
        )
        read_only_fields = (
            'id', 'is_moderated', 'is_approved', 'created_at', 'updated_at'
        )

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value


class ReviewCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating reviews"""

    class Meta:
        model = Review
        fields = ('event', 'rating', 'title', 'content')

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value

    def validate(self, attrs):
        """Validate that user hasn't already reviewed this event"""
        user = self.context['request'].user
        event = attrs.get('event')

        # Only check for duplicates when creating (not updating)
        if not self.instance:
            if Review.objects.filter(user=user, event=event).exists():
                raise serializers.ValidationError(
                    {"event": "You have already reviewed this event."}
                )

        return attrs
