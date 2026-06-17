from django.contrib import admin, messages
from django.db.models import QuerySet
from django.http import HttpRequest

from .models import CartItem, Order, OrderItem
from .services import cancel_order


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ("user", "product", "quantity")


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product", "quantity", "price")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "status", "total_price", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("full_name", "email")
    inlines = (OrderItemInline,)
    actions = ("mark_shipped", "mark_delivered", "cancel_orders")

    @admin.action(description="Позначити відправленими")
    def mark_shipped(self, request: HttpRequest, queryset: QuerySet[Order]) -> None:
        queryset.update(status=Order.Status.SHIPPED)

    @admin.action(description="Позначити доставленими")
    def mark_delivered(self, request: HttpRequest, queryset: QuerySet[Order]) -> None:
        queryset.update(status=Order.Status.DELIVERED)

    @admin.action(description="Скасувати (повернути залишки)")
    def cancel_orders(self, request: HttpRequest, queryset: QuerySet[Order]) -> None:
        for order in queryset:
            cancel_order(order)
        self.message_user(request, "Замовлення скасовано, залишки повернено.", messages.SUCCESS)
