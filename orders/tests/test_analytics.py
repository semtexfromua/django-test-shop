"""Тести адмін-аналітики, скасування та ролей."""
from decimal import Decimal
from typing import cast

import pytest
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.test import Client
from django.urls import reverse

from orders import analytics
from orders.models import Order, OrderItem
from orders.services import cancel_order
from products.models import Product
from products.tests.factories import ProductFactory
from users.models import User
from users.tests.factories import UserFactory


def _order(user: User, status: str, total: Decimal) -> Order:
    return Order.objects.create(
        user=user,
        status=status,
        full_name="b",
        email="b@e.com",
        phone="1",
        shipping_address="a",
        total_price=total,
    )


@pytest.mark.django_db
def test_total_revenue_counts_only_fulfilled() -> None:
    user = cast(User, UserFactory())
    _order(user, Order.Status.PAID, Decimal("100"))
    _order(user, Order.Status.PENDING, Decimal("50"))
    _order(user, Order.Status.DELIVERED, Decimal("20"))
    assert analytics.total_revenue() == Decimal("120")


@pytest.mark.django_db
def test_top_products_ranks_by_units_sold() -> None:
    user = cast(User, UserFactory())
    p1 = cast(Product, ProductFactory(name="A"))
    p2 = cast(Product, ProductFactory(name="B"))
    order = _order(user, Order.Status.PAID, Decimal("0"))
    OrderItem.objects.create(order=order, product=p1, quantity=5, price=Decimal("1"))
    OrderItem.objects.create(order=order, product=p2, quantity=2, price=Decimal("1"))
    top = analytics.top_products()
    assert top[0]["product__name"] == "A"
    assert top[0]["sold"] == 5


@pytest.mark.django_db
def test_cancel_order_restores_stock() -> None:
    user = cast(User, UserFactory())
    product = cast(Product, ProductFactory(stock=1))
    order = _order(user, Order.Status.PAID, Decimal("10"))
    OrderItem.objects.create(order=order, product=product, quantity=2, price=Decimal("5"))
    cancel_order(order)
    product.refresh_from_db()
    order.refresh_from_db()
    assert product.stock == 3
    assert order.status == Order.Status.CANCELLED


@pytest.mark.django_db
def test_cancel_order_idempotent() -> None:
    user = cast(User, UserFactory())
    product = cast(Product, ProductFactory(stock=1))
    order = _order(user, Order.Status.PAID, Decimal("10"))
    OrderItem.objects.create(order=order, product=product, quantity=2, price=Decimal("5"))
    cancel_order(order)
    cancel_order(order)  # повторне скасування не має повернути stock удруге
    product.refresh_from_db()
    assert product.stock == 3
    assert order.status == Order.Status.CANCELLED


@pytest.mark.django_db
def test_orders_by_status_counts() -> None:
    user = cast(User, UserFactory())
    _order(user, Order.Status.PAID, Decimal("1"))
    _order(user, Order.Status.PAID, Decimal("1"))
    _order(user, Order.Status.PENDING, Decimal("1"))
    by_status = analytics.orders_by_status()
    assert by_status["Оплачено"] == 2
    assert by_status["Очікує"] == 1
    assert analytics.order_count() == 3


@pytest.mark.django_db
def test_dashboard_requires_staff(client: Client) -> None:
    assert client.get(reverse("orders:analytics")).status_code == 302
    user = cast(User, UserFactory())
    client.force_login(user)
    assert client.get(reverse("orders:analytics")).status_code == 403
    staff = cast(User, UserFactory(is_staff=True))
    client.force_login(staff)
    assert client.get(reverse("orders:analytics")).status_code == 200


@pytest.mark.django_db
def test_setup_roles_idempotent() -> None:
    call_command("setup_roles")
    call_command("setup_roles")
    assert Group.objects.filter(name="Managers").count() == 1
