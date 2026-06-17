from decimal import Decimal
from typing import cast

import pytest

from orders.models import Order
from orders.tests.factories import OrderFactory
from payments.models import Payment


@pytest.mark.django_db
def test_payment_str() -> None:
    order = cast(Order, OrderFactory())
    payment = Payment.objects.create(order=order, method=Payment.Method.CARD, amount=Decimal("10"))
    assert str(payment).startswith("Оплата")
