from django.contrib import admin
from .models import EventCategory, Event, EventFavorite, EventComment


@admin.register(EventCategory)
class EventCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'organizer', 'category', 'venue_name', 'city', 'start_date', 'status', 'privacy', 'capacity', 'view_count', 'created_at')
    list_filter = ('status', 'privacy', 'category', 'city', 'country', 'created_at')
    search_fields = ('title', 'description', 'organizer__email', 'venue_name', 'city')
    prepopulated_fields = {'slug': ('title',)}
    ordering = ('-start_date',)
    readonly_fields = ('view_count', 'created_at', 'updated_at')
    date_hierarchy = 'start_date'

    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'description', 'organizer', 'category', 'status', 'privacy')
        }),
        ('Location', {
            'fields': ('venue_name', 'venue_address', 'city', 'state', 'country', 'latitude', 'longitude')
        }),
        ('Timing & Capacity', {
            'fields': ('start_date', 'end_date', 'capacity')
        }),
        ('Media', {
            'fields': ('banner_image', 'thumbnail_image')
        }),
        ('Metadata', {
            'fields': ('tags', 'view_count', 'created_at', 'updated_at')
        }),
    )


@admin.register(EventFavorite)
class EventFavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'event', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__email', 'event__title')
    ordering = ('-created_at',)


@admin.register(EventComment)
class EventCommentAdmin(admin.ModelAdmin):
    list_display = ('event', 'user', 'content_preview', 'parent', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('event__title', 'user__email', 'content')
    ordering = ('-created_at',)

    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'
