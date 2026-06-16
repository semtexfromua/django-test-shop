"""Order model tests."""
from decimal import Decimal
from typing import cast

import pytest

from orders.models import Order, OrderItem
from orders.tests.factories import OrderFactory, OrderItemFactory


@pytest.mark.django_db
def test_order_str() -> None:
    order = cast(Order, OrderFactory())
    assert str(order) == f"Замовлення #{order.pk}"


@pytest.mark.django_db
def test_orderitem_subtotal() -> None:
    item = cast(OrderItem, OrderItemFactory(quantity=3, price=Decimal("10.00")))
    assert item.subtotal == Decimal("30.00")
