"""Order email Celery task tests (run eagerly)."""
from decimal import Decimal
from typing import cast

import pytest
from django.core import mail
from django.test import override_settings

from orders.models import Order, OrderItem
from orders.tasks import send_order_email
from products.models import Product
from products.tests.factories import ProductFactory
from users.models import User
from users.tests.factories import UserFactory


def _order(user: User) -> Order:
    order = Order.objects.create(
        user=user, status=Order.Status.PAID, full_name="Buyer", email="b@e.com",
        phone="1", shipping_address="addr", total_price=Decimal("20.00"),
    )
    product = cast(Product, ProductFactory(price=Decimal("10.00"), stock=48))
    OrderItem.objects.create(order=order, product=product, quantity=2, price=Decimal("10.00"))
    return order


@pytest.mark.django_db
@override_settings(DEFAULT_FROM_EMAIL="shop@shop.test")
def test_send_order_email_customer() -> None:
    order = _order(cast(User, UserFactory()))
    send_order_email(order.pk, "customer")
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ["b@e.com"]
    assert f"#{order.pk}" in mail.outbox[0].subject


@pytest.mark.django_db
@override_settings(ADMINS=[("Admin", "admin@shop.test")])
def test_send_order_email_admin() -> None:
    order = _order(cast(User, UserFactory()))
    send_order_email(order.pk, "admin")
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ["admin@shop.test"]
