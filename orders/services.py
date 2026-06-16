"""Бізнес-логіка створення замовлення.

Свідомо НЕ залежить від payments (інакше цикл orders↔payments): оплату
підв'язує в'юха checkout. Email надсилається тут — замовлення прийнято.
"""
from dataclasses import dataclass
from decimal import Decimal

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction

from products.models import Product
from users.models import User

from .models import Order, OrderItem


@dataclass(frozen=True)
class OrderContact:
    full_name: str
    email: str
    phone: str
    shipping_address: str


class InsufficientStock(Exception):
    def __init__(self, product: Product, available: int) -> None:
        self.product = product
        self.available = available
        super().__init__(f"Недостатньо «{product.name}»: доступно {available} шт.")


def create_order(user: User, items: list[tuple[Product, int]], contact: OrderContact) -> Order:
    """Атомарно: знімок цін, перевірка та списання залишків, email на commit."""
    with transaction.atomic():
        ids = [product.pk for product, _ in items]
        locked = {p.pk: p for p in Product.objects.select_for_update().filter(pk__in=ids)}
        order = Order.objects.create(
            user=user,
            full_name=contact.full_name,
            email=contact.email,
            phone=contact.phone,
            shipping_address=contact.shipping_address,
        )
        total = Decimal("0")
        for product, quantity in items:
            locked_product = locked[product.pk]
            if quantity > locked_product.stock:
                raise InsufficientStock(locked_product, locked_product.stock)
            OrderItem.objects.create(
                order=order,
                product=locked_product,
                quantity=quantity,
                price=locked_product.price,
            )
            locked_product.stock -= quantity
            locked_product.save(update_fields=["stock"])
            total += locked_product.price * quantity
        order.total_price = total
        order.save(update_fields=["total_price"])
        transaction.on_commit(lambda: _send_order_emails(order))
    return order


def _send_order_emails(order: Order) -> None:
    body = f"Дякуємо! Замовлення #{order.pk} на суму ${order.total_price} прийнято."
    send_mail(
        f"Замовлення #{order.pk}", body, settings.DEFAULT_FROM_EMAIL, [order.email],
        fail_silently=True,
    )
    admin_emails = [email for _, email in settings.ADMINS]
    if admin_emails:
        send_mail(
            f"Нове замовлення #{order.pk}", body, settings.DEFAULT_FROM_EMAIL, admin_emails,
            fail_silently=True,
        )
