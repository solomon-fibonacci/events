from django.db import models
from django.utils.translation import gettext_lazy as _
from users.models import User
from events.models import Event
import uuid


class MenuCategory(models.Model):
    """Categories for menu items (Appetizers, Entrees, Desserts, Beverages)"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Menu Categories'
        ordering = ['display_order', 'name']

    def __str__(self):
        return self.name


class Menu(models.Model):
    """Menu for an event"""
    event = models.OneToOneField(
        Event,
        on_delete=models.CASCADE,
        related_name='menu'
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    vendor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='vendor_menus',
        limit_choices_to={'role': 'vendor'}
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.event.title} - {self.name}"


class MenuItem(models.Model):
    """Individual menu items (food/drink)"""

    class DietaryType(models.TextChoices):
        VEGETARIAN = 'vegetarian', _('Vegetarian')
        VEGAN = 'vegan', _('Vegan')
        GLUTEN_FREE = 'gluten_free', _('Gluten Free')
        HALAL = 'halal', _('Halal')
        KOSHER = 'kosher', _('Kosher')
        NONE = 'none', _('None')

    menu = models.ForeignKey(
        Menu,
        on_delete=models.CASCADE,
        related_name='items'
    )
    category = models.ForeignKey(
        MenuCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='items'
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='menu_items/', blank=True, null=True)

    # Dietary information
    dietary_type = models.CharField(
        max_length=20,
        choices=DietaryType.choices,
        default=DietaryType.NONE
    )
    allergen_info = models.CharField(max_length=500, blank=True, null=True)

    # Availability
    is_available = models.BooleanField(default=True)
    stock_quantity = models.PositiveIntegerField(null=True, blank=True)

    # Metadata
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'display_order', 'name']

    def __str__(self):
        return f"{self.menu.event.title} - {self.name}"

    @property
    def in_stock(self):
        if self.stock_quantity is None:
            return True
        return self.stock_quantity > 0


class FoodOrder(models.Model):
    """Order for food/drinks at an event"""

    class Status(models.TextChoices):
        PENDING = 'pending', _('Pending')
        CONFIRMED = 'confirmed', _('Confirmed')
        PREPARING = 'preparing', _('Preparing')
        READY = 'ready', _('Ready')
        DELIVERED = 'delivered', _('Delivered')
        CANCELLED = 'cancelled', _('Cancelled')

    order_number = models.CharField(max_length=50, unique=True)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='food_orders'
    )
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='food_orders'
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    # Pricing
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    service_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    # Payment (Stripe)
    stripe_payment_intent_id = models.CharField(max_length=200, blank=True, null=True)
    stripe_charge_id = models.CharField(max_length=200, blank=True, null=True)

    # Delivery notes
    notes = models.TextField(blank=True, null=True)
    table_number = models.CharField(max_length=50, blank=True, null=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order_number']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['event', 'status']),
        ]

    def __str__(self):
        return f"Food Order {self.order_number} - {self.user.email}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()
        super().save(*args, **kwargs)

    @staticmethod
    def generate_order_number():
        return f"FO-{uuid.uuid4().hex[:12].upper()}"


class FoodOrderItem(models.Model):
    """Individual items in a food order"""
    food_order = models.ForeignKey(
        FoodOrder,
        on_delete=models.CASCADE,
        related_name='items'
    )
    menu_item = models.ForeignKey(
        MenuItem,
        on_delete=models.CASCADE,
        related_name='order_items'
    )
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    special_instructions = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.quantity}x {self.menu_item.name}"

    def save(self, *args, **kwargs):
        self.total_price = self.unit_price * self.quantity
        super().save(*args, **kwargs)
