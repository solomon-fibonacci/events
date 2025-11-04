from django.contrib import admin
from .models import TicketType, Order, Registration, Refund


@admin.register(TicketType)
class TicketTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'event', 'price', 'quantity', 'quantity_sold', 'quantity_remaining', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'event__title')
    ordering = ('-created_at',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'user', 'event', 'status', 'total', 'created_at', 'paid_at')
    list_filter = ('status', 'created_at', 'paid_at')
    search_fields = ('order_number', 'user__email', 'event__title')
    ordering = ('-created_at',)
    readonly_fields = ('order_number', 'created_at', 'updated_at')


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ('ticket_number', 'user', 'event', 'ticket_type', 'status', 'created_at', 'checked_in_at')
    list_filter = ('status', 'created_at', 'checked_in_at')
    search_fields = ('ticket_number', 'user__email', 'event__title')
    ordering = ('-created_at',)
    readonly_fields = ('ticket_number', 'qr_code_data', 'created_at', 'updated_at')


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ('order', 'user', 'amount', 'status', 'created_at', 'completed_at')
    list_filter = ('status', 'created_at')
    search_fields = ('order__order_number', 'user__email')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
