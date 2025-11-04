from django.contrib import admin
from .models import MenuCategory, Menu, MenuItem, FoodOrder, FoodOrderItem


@admin.register(MenuCategory)
class MenuCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_order', 'created_at')
    search_fields = ('name',)
    ordering = ('display_order', 'name')


@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    list_display = ('name', 'event', 'vendor', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'event__title', 'vendor__email')
    ordering = ('-created_at',)


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'menu', 'category', 'price', 'dietary_type', 'is_available', 'stock_quantity', 'display_order')
    list_filter = ('is_available', 'dietary_type', 'category', 'created_at')
    search_fields = ('name', 'menu__name', 'menu__event__title')
    ordering = ('menu', 'display_order', 'name')


class FoodOrderItemInline(admin.TabularInline):
    model = FoodOrderItem
    extra = 0
    readonly_fields = ('total_price',)


@admin.register(FoodOrder)
class FoodOrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'user', 'event', 'status', 'total', 'table_number', 'created_at', 'paid_at')
    list_filter = ('status', 'created_at', 'paid_at')
    search_fields = ('order_number', 'user__email', 'event__title', 'table_number')
    ordering = ('-created_at',)
    readonly_fields = ('order_number', 'created_at', 'updated_at')
    inlines = [FoodOrderItemInline]


@admin.register(FoodOrderItem)
class FoodOrderItemAdmin(admin.ModelAdmin):
    list_display = ('food_order', 'menu_item', 'quantity', 'unit_price', 'total_price', 'created_at')
    search_fields = ('food_order__order_number', 'menu_item__name')
    ordering = ('-created_at',)
    readonly_fields = ('total_price',)
