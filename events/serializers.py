from rest_framework import serializers
from .models import EventCategory, Event, EventFavorite, EventComment
from users.serializers import UserSerializer


class EventCategorySerializer(serializers.ModelSerializer):
    """Serializer for EventCategory model"""

    class Meta:
        model = EventCategory
        fields = ('id', 'name', 'slug', 'description', 'icon', 'created_at')
        read_only_fields = ('id', 'created_at')


class EventListSerializer(serializers.ModelSerializer):
    """Serializer for listing events (minimal data)"""
    organizer = UserSerializer(read_only=True)
    category = EventCategorySerializer(read_only=True)
    is_upcoming = serializers.ReadOnlyField()
    is_ongoing = serializers.ReadOnlyField()
    is_past = serializers.ReadOnlyField()
    available_tickets = serializers.ReadOnlyField()

    class Meta:
        model = Event
        fields = (
            'id', 'title', 'slug', 'organizer', 'category', 'venue_name', 'city',
            'country', 'start_date', 'end_date', 'capacity', 'status', 'privacy',
            'thumbnail_image', 'view_count', 'is_upcoming', 'is_ongoing', 'is_past',
            'available_tickets', 'created_at'
        )
        read_only_fields = ('id', 'view_count', 'created_at')


class EventDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed event view"""
    organizer = UserSerializer(read_only=True)
    category = EventCategorySerializer(read_only=True)
    is_upcoming = serializers.ReadOnlyField()
    is_ongoing = serializers.ReadOnlyField()
    is_past = serializers.ReadOnlyField()
    available_tickets = serializers.ReadOnlyField()

    class Meta:
        model = Event
        fields = (
            'id', 'title', 'slug', 'description', 'organizer', 'category',
            'venue_name', 'venue_address', 'city', 'state', 'country',
            'latitude', 'longitude', 'start_date', 'end_date', 'capacity',
            'status', 'privacy', 'banner_image', 'thumbnail_image', 'tags',
            'view_count', 'is_upcoming', 'is_ongoing', 'is_past',
            'available_tickets', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'view_count', 'created_at', 'updated_at')


class EventCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating events"""

    class Meta:
        model = Event
        fields = (
            'title', 'slug', 'description', 'category', 'venue_name',
            'venue_address', 'city', 'state', 'country', 'latitude',
            'longitude', 'start_date', 'end_date', 'capacity', 'status',
            'privacy', 'banner_image', 'thumbnail_image', 'tags'
        )

    def validate(self, attrs):
        if 'start_date' in attrs and 'end_date' in attrs:
            if attrs['start_date'] >= attrs['end_date']:
                raise serializers.ValidationError({
                    "end_date": "End date must be after start date."
                })
        return attrs


class EventFavoriteSerializer(serializers.ModelSerializer):
    """Serializer for EventFavorite model"""
    event = EventListSerializer(read_only=True)
    user = UserSerializer(read_only=True)

    class Meta:
        model = EventFavorite
        fields = ('id', 'user', 'event', 'created_at')
        read_only_fields = ('id', 'created_at')


class EventCommentSerializer(serializers.ModelSerializer):
    """Serializer for EventComment model"""
    user = UserSerializer(read_only=True)
    replies = serializers.SerializerMethodField()

    class Meta:
        model = EventComment
        fields = ('id', 'event', 'user', 'content', 'parent', 'replies', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')

    def get_replies(self, obj):
        if obj.replies.exists():
            return EventCommentSerializer(obj.replies.all(), many=True).data
        return []
