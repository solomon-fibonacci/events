from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from users.models import User
from events.models import Event


class Review(models.Model):
    """Reviews and ratings for events"""
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text='Rating from 1 to 5 stars'
    )
    title = models.CharField(max_length=200, blank=True, null=True)
    content = models.TextField()
    is_moderated = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=True)
    moderated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='moderated_reviews'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('event', 'user')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['event', 'is_approved']),
        ]

    def __str__(self):
        return f"Review by {self.user.email} for {self.event.title} - {self.rating} stars"
