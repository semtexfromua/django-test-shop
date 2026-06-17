from django.db import models

from orders.models import Order


class Payment(models.Model):
    class Method(models.TextChoices):
        CARD = "card", "Картка"
        CASH = "cash", "Готівка при отриманні"

    class Status(models.TextChoices):
        PENDING = "pending", "Очікує"
        PAID = "paid", "Оплачено"
        FAILED = "failed", "Помилка"

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="payment")
    method = models.CharField(max_length=20, choices=Method.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_id = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Оплата {self.order} — {self.get_status_display()}"
