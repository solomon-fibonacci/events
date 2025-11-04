from django.contrib import admin
from .models import EmailNotification


@admin.register(EmailNotification)
class EmailNotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'notification_type', 'event', 'status', 'subject', 'sent_at', 'created_at')
    list_filter = ('notification_type', 'status', 'created_at', 'sent_at')
    search_fields = ('recipient__email', 'event__title', 'subject', 'message')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)
