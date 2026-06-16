"""Моделі замовлень."""
from decimal import Decimal

from django.conf import settings
from django.db import models

from products.models import Product


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Очікує"
        PAID = "paid", "Оплачено"
        SHIPPED = "shipped", "Відправлено"
        DELIVERED = "delivered", "Доставлено"
        CANCELLED = "cancelled", "Скасовано"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="orders"
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0"))
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=32)
    shipping_address = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Замовлення #{self.pk}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="order_items")
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self) -> str:
        return f"{self.quantity}× {self.product.name}"

    @property
    def subtotal(self) -> Decimal:
        return self.price * self.quantity
