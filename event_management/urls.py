"""
URL configuration for event_management project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

from .api_views import (
    EventViewSet, EventCategoryViewSet, EventCommentViewSet,
    TicketOrderView, MyTicketsView, CheckInView,
    MenuViewSet, FoodOrderView, ReviewViewSet, EventAnalyticsView
)

# Swagger Schema
schema_view = get_schema_view(
    openapi.Info(
        title="Event Management API",
        default_version='v1',
        description="Comprehensive Event Management System API with ticketing, food ordering, and more",
        terms_of_service="https://www.example.com/terms/",
        contact=openapi.Contact(email="contact@eventmanagement.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

# Create router
router = DefaultRouter()
router.register(r'events', EventViewSet, basename='event')
router.register(r'categories', EventCategoryViewSet, basename='category')
router.register(r'comments', EventCommentViewSet, basename='comment')
router.register(r'menus', MenuViewSet, basename='menu')
router.register(r'reviews', ReviewViewSet, basename='review')

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),

    # API Documentation
    path('api/docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('api/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    # API Routes
    path('api/', include(router.urls)),
    path('api/users/', include('users.urls')),

    # Tickets
    path('api/tickets/order/', TicketOrderView.as_view(), name='ticket-order'),
    path('api/tickets/my-tickets/', MyTicketsView.as_view(), name='my-tickets'),
    path('api/tickets/check-in/', CheckInView.as_view(), name='check-in'),

    # Food Orders
    path('api/food/order/', FoodOrderView.as_view(), name='food-order'),

    # Analytics
    path('api/analytics/event/<int:event_id>/', EventAnalyticsView.as_view(), name='event-analytics'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
