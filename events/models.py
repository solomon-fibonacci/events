from django.db import models
from django.utils.translation import gettext_lazy as _
from users.models import User


class EventCategory(models.Model):
    """Categories for events (Conference, Concert, Workshop, etc.)"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    icon = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Event Categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class Event(models.Model):
    """Main Event model"""

    class Status(models.TextChoices):
        DRAFT = 'draft', _('Draft')
        PUBLISHED = 'published', _('Published')
        CANCELLED = 'cancelled', _('Cancelled')
        COMPLETED = 'completed', _('Completed')

    class Privacy(models.TextChoices):
        PUBLIC = 'public', _('Public')
        PRIVATE = 'private', _('Private')
        INVITE_ONLY = 'invite_only', _('Invite Only')

    # Basic Information
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField()
    organizer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='organized_events'
    )
    category = models.ForeignKey(
        EventCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='events'
    )

    # Location & Timing
    venue_name = models.CharField(max_length=200)
    venue_address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    # Capacity & Status
    capacity = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    privacy = models.CharField(max_length=20, choices=Privacy.choices, default=Privacy.PUBLIC)

    # Media
    banner_image = models.ImageField(upload_to='events/banners/', blank=True, null=True)
    thumbnail_image = models.ImageField(upload_to='events/thumbnails/', blank=True, null=True)

    # Tags
    tags = models.CharField(max_length=500, blank=True, help_text='Comma-separated tags')

    # Metadata
    view_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['status', 'privacy', 'start_date']),
            models.Index(fields=['city', 'country']),
            models.Index(fields=['slug']),
        ]

    def __str__(self):
        return self.title

    @property
    def is_upcoming(self):
        from django.utils import timezone
        return self.start_date > timezone.now()

    @property
    def is_ongoing(self):
        from django.utils import timezone
        now = timezone.now()
        return self.start_date <= now <= self.end_date

    @property
    def is_past(self):
        from django.utils import timezone
        return self.end_date < timezone.now()

    @property
    def available_tickets(self):
        from tickets.models import Registration
        registered_count = Registration.objects.filter(
            event=self,
            status__in=['confirmed', 'checked_in']
        ).count()
        return self.capacity - registered_count


class EventFavorite(models.Model):
    """User favorites/bookmarks for events"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorite_events'
    )
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='favorited_by'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'event')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} favorited {self.event.title}"


class EventComment(models.Model):
    """Comments/Q&A for events"""
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='event_comments'
    )
    content = models.TextField()
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.user.email} on {self.event.title}"
