from django.conf import settings
from django.contrib import admin, messages
from django.db.models import QuerySet
from django.http import HttpRequest

from .models import CartItem, Order, OrderItem
from .services import cancel_order
from .tasks import send_order_email


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
    actions = ("mark_shipped", "mark_delivered", "cancel_orders", "resend_emails")

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

    @admin.action(description="Надіслати листи ще раз")
    def resend_emails(self, request: HttpRequest, queryset: QuerySet[Order]) -> None:
        has_admins = any(email for _, email in settings.ADMINS)
        for order in queryset:
            send_order_email.delay(order.pk, "customer")
            if has_admins:
                send_order_email.delay(order.pk, "admin")
        self.message_user(
            request, "Листи поставлено в чергу на повторну відправку.", messages.SUCCESS
        )
