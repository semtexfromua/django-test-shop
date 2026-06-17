"""Order creation business logic.

Deliberately does NOT depend on payments (otherwise an orders↔payments cycle):
payment is wired up by the checkout view. Email is sent here — order accepted.
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
    """Atomically: price snapshot, stock check and decrement, email on commit.

    Concurrent orders are serialized by row-level ``select_for_update``;
    tests cover sequential overselling (not parallel).
    """
    with transaction.atomic():
        ids = [product.pk for product, _ in items]
        # active only: a product deactivated after being added to the cart is not sold
        locked = {
            p.pk: p
            for p in Product.objects.select_for_update().filter(pk__in=ids, is_active=True)
        }
        order = Order.objects.create(
            user=user,
            full_name=contact.full_name,
            email=contact.email,
            phone=contact.phone,
            shipping_address=contact.shipping_address,
        )
        total = Decimal("0")
        for product, quantity in items:
            locked_product = locked.get(product.pk)
            if locked_product is None:
                raise InsufficientStock(product, 0)
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
    customer_body = f"Дякуємо! Замовлення #{order.pk} на суму ${order.total_price} прийнято."
    send_mail(
        f"Замовлення #{order.pk}", customer_body, settings.DEFAULT_FROM_EMAIL, [order.email],
        fail_silently=True,
    )
    admin_emails = [email for _, email in settings.ADMINS]
    if admin_emails:
        admin_body = (
            f"Нове замовлення #{order.pk} на суму ${order.total_price} "
            f"(покупець: {order.email})."
        )
        send_mail(
            f"Нове замовлення #{order.pk}", admin_body, settings.DEFAULT_FROM_EMAIL, admin_emails,
            fail_silently=True,
        )


def cancel_order(order: Order) -> None:
    """Cancel an order and restore stock (idempotent)."""
    if order.status == Order.Status.CANCELLED:
        return
    with transaction.atomic():
        for item in order.items.select_related("product"):
            product = item.product
            product.stock += item.quantity
            product.save(update_fields=["stock"])
        order.status = Order.Status.CANCELLED
        order.save(update_fields=["status"])
