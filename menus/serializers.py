from rest_framework import serializers
from .models import MenuCategory, Menu, MenuItem, FoodOrder, FoodOrderItem
from users.serializers import UserSerializer
from events.serializers import EventListSerializer


class MenuCategorySerializer(serializers.ModelSerializer):
    """Serializer for MenuCategory model"""

    class Meta:
        model = MenuCategory
        fields = ('id', 'name', 'description', 'display_order', 'created_at')
        read_only_fields = ('id', 'created_at')


class MenuItemSerializer(serializers.ModelSerializer):
    """Serializer for MenuItem model"""
    category = MenuCategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=MenuCategory.objects.all(),
        source='category',
        write_only=True,
        required=False
    )
    in_stock = serializers.ReadOnlyField()

    class Meta:
        model = MenuItem
        fields = (
            'id', 'menu', 'category', 'category_id', 'name', 'description',
            'price', 'image', 'dietary_type', 'allergen_info', 'is_available',
            'stock_quantity', 'in_stock', 'display_order', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


class MenuSerializer(serializers.ModelSerializer):
    """Serializer for Menu model"""
    event = EventListSerializer(read_only=True)
    vendor = UserSerializer(read_only=True)
    items = MenuItemSerializer(many=True, read_only=True)

    class Meta:
        model = Menu
        fields = (
            'id', 'event', 'name', 'description', 'is_active', 'vendor',
            'items', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


class FoodOrderItemSerializer(serializers.ModelSerializer):
    """Serializer for FoodOrderItem model"""
    menu_item = MenuItemSerializer(read_only=True)
    menu_item_id = serializers.PrimaryKeyRelatedField(
        queryset=MenuItem.objects.all(),
        source='menu_item',
        write_only=True
    )

    class Meta:
        model = FoodOrderItem
        fields = (
            'id', 'menu_item', 'menu_item_id', 'quantity', 'unit_price',
            'total_price', 'special_instructions', 'created_at'
        )
        read_only_fields = ('id', 'total_price', 'created_at')


class FoodOrderSerializer(serializers.ModelSerializer):
    """Serializer for FoodOrder model"""
    user = UserSerializer(read_only=True)
    event = EventListSerializer(read_only=True)
    items = FoodOrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = FoodOrder
        fields = (
            'id', 'order_number', 'user', 'event', 'status', 'subtotal',
            'tax', 'service_fee', 'total', 'stripe_payment_intent_id',
            'notes', 'table_number', 'items', 'created_at', 'updated_at',
            'paid_at', 'completed_at'
        )
        read_only_fields = (
            'id', 'order_number', 'stripe_payment_intent_id', 'created_at',
            'updated_at', 'paid_at', 'completed_at'
        )


class FoodOrderCreateSerializer(serializers.Serializer):
    """Serializer for creating a food order"""
    event_id = serializers.IntegerField(required=True)
    items = serializers.ListField(
        child=serializers.DictField(),
        required=True,
        help_text="List of item objects with menu_item_id, quantity, and optional special_instructions"
    )
    notes = serializers.CharField(required=False, allow_blank=True)
    table_number = serializers.CharField(required=False, allow_blank=True)

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("At least one item must be selected.")
        for item in value:
            if 'menu_item_id' not in item or 'quantity' not in item:
                raise serializers.ValidationError(
                    "Each item must have menu_item_id and quantity."
                )
            if item['quantity'] < 1:
                raise serializers.ValidationError("Quantity must be at least 1.")
        return value
