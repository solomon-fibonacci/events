from django.db import models
from django.utils.translation import gettext_lazy as _
from users.models import User
from events.models import Event


class EmailNotification(models.Model):
    """Track sent email notifications"""

    class NotificationType(models.TextChoices):
        EMAIL_VERIFICATION = 'email_verification', _('Email Verification')
        PASSWORD_RESET = 'password_reset', _('Password Reset')
        REGISTRATION_CONFIRMATION = 'registration_confirmation', _('Registration Confirmation')
        TICKET_RECEIPT = 'ticket_receipt', _('Ticket Receipt')
        EVENT_REMINDER = 'event_reminder', _('Event Reminder')
        EVENT_UPDATE = 'event_update', _('Event Update')
        EVENT_CANCELLED = 'event_cancelled', _('Event Cancelled')
        FOOD_ORDER_CONFIRMATION = 'food_order_confirmation', _('Food Order Confirmation')
        FOOD_ORDER_READY = 'food_order_ready', _('Food Order Ready')

    class Status(models.TextChoices):
        PENDING = 'pending', _('Pending')
        SENT = 'sent', _('Sent')
        FAILED = 'failed', _('Failed')

    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications'
    )
    notification_type = models.CharField(max_length=50, choices=NotificationType.choices)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    error_message = models.TextField(blank=True, null=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'notification_type']),
            models.Index(fields=['event', 'notification_type']),
        ]

    def __str__(self):
        return f"{self.notification_type} to {self.recipient.email}"
