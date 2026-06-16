"""Тести мок-оплати."""
from decimal import Decimal
from typing import cast

import pytest

from orders.models import Order
from orders.services import OrderContact, create_order
from payments.models import Payment
from payments.services import process_payment
from products.models import Product
from products.tests.factories import ProductFactory
from users.models import User
from users.tests.factories import UserFactory


@pytest.mark.django_db
def test_process_payment_marks_paid() -> None:
    user = cast(User, UserFactory())
    p = cast(Product, ProductFactory(price=Decimal("10.00"), stock=5))
    order = create_order(
        user, [(p, 1)],
        OrderContact(full_name="B", email="b@e.com", phone="1", shipping_address="a"),
    )
    payment = process_payment(order, "card")
    assert payment.status == Payment.Status.PAID
    assert payment.amount == Decimal("10.00")
    order.refresh_from_db()
    assert order.status == Order.Status.PAID
