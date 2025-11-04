from django.contrib import admin
from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('event', 'user', 'rating', 'is_approved', 'is_moderated', 'created_at')
    list_filter = ('rating', 'is_approved', 'is_moderated', 'created_at')
    search_fields = ('event__title', 'user__email', 'title', 'content')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
