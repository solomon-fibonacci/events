from rest_framework import serializers
from .models import TicketType, Order, Registration, Refund
from users.serializers import UserSerializer
from events.serializers import EventListSerializer


class TicketTypeSerializer(serializers.ModelSerializer):
    """Serializer for TicketType model"""
    is_available = serializers.ReadOnlyField()
    quantity_remaining = serializers.ReadOnlyField()

    class Meta:
        model = TicketType
        fields = (
            'id', 'event', 'name', 'description', 'price', 'quantity',
            'quantity_sold', 'is_available', 'quantity_remaining', 'is_active',
            'sale_start_date', 'sale_end_date', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'quantity_sold', 'created_at', 'updated_at')


class OrderSerializer(serializers.ModelSerializer):
    """Serializer for Order model"""
    user = UserSerializer(read_only=True)
    event = EventListSerializer(read_only=True)

    class Meta:
        model = Order
        fields = (
            'id', 'order_number', 'user', 'event', 'status', 'subtotal',
            'tax', 'service_fee', 'total', 'stripe_payment_intent_id',
            'payment_method', 'created_at', 'updated_at', 'paid_at'
        )
        read_only_fields = (
            'id', 'order_number', 'stripe_payment_intent_id', 'created_at',
            'updated_at', 'paid_at'
        )


class OrderCreateSerializer(serializers.Serializer):
    """Serializer for creating an order"""
    event_id = serializers.IntegerField(required=True)
    tickets = serializers.ListField(
        child=serializers.DictField(child=serializers.IntegerField()),
        required=True,
        help_text="List of ticket objects with ticket_type_id and quantity"
    )

    def validate_tickets(self, value):
        if not value:
            raise serializers.ValidationError("At least one ticket must be selected.")
        for ticket in value:
            if 'ticket_type_id' not in ticket or 'quantity' not in ticket:
                raise serializers.ValidationError(
                    "Each ticket must have ticket_type_id and quantity."
                )
            if ticket['quantity'] < 1:
                raise serializers.ValidationError("Quantity must be at least 1.")
        return value


class RegistrationSerializer(serializers.ModelSerializer):
    """Serializer for Registration model"""
    user = UserSerializer(read_only=True)
    event = EventListSerializer(read_only=True)
    ticket_type = TicketTypeSerializer(read_only=True)
    order = OrderSerializer(read_only=True)

    class Meta:
        model = Registration
        fields = (
            'id', 'ticket_number', 'order', 'event', 'user', 'ticket_type',
            'status', 'qr_code', 'qr_code_data', 'checked_in_at',
            'checked_in_by', 'created_at', 'updated_at'
        )
        read_only_fields = (
            'id', 'ticket_number', 'qr_code', 'qr_code_data', 'created_at',
            'updated_at'
        )


class CheckInSerializer(serializers.Serializer):
    """Serializer for checking in a ticket"""
    ticket_number = serializers.CharField(required=True)


class RefundSerializer(serializers.ModelSerializer):
    """Serializer for Refund model"""
    user = UserSerializer(read_only=True)
    order = OrderSerializer(read_only=True)

    class Meta:
        model = Refund
        fields = (
            'id', 'order', 'user', 'amount', 'reason', 'status',
            'stripe_refund_id', 'admin_notes', 'processed_by',
            'created_at', 'updated_at', 'completed_at'
        )
        read_only_fields = (
            'id', 'stripe_refund_id', 'created_at', 'updated_at', 'completed_at'
        )


class RefundCreateSerializer(serializers.Serializer):
    """Serializer for creating a refund request"""
    order_id = serializers.IntegerField(required=True)
    reason = serializers.CharField(required=True)
