"""Тести оформлення замовлення та історії."""
from decimal import Decimal
from typing import cast

import pytest
from django.test import Client
from django.urls import reverse

from orders.models import Order
from orders.tests.factories import OrderFactory
from products.models import Product
from products.tests.factories import ProductFactory
from users.models import User
from users.tests.factories import UserFactory


@pytest.mark.django_db
def test_checkout_requires_login(client: Client) -> None:
    resp = client.get(reverse("orders:checkout"))
    assert resp.status_code == 302
    assert reverse("users:login") in resp["Location"]


@pytest.mark.django_db
def test_checkout_creates_paid_order_and_clears_cart(client: Client) -> None:
    user = cast(User, UserFactory())
    client.force_login(user)
    product = cast(Product, ProductFactory(price=Decimal("10.00"), stock=5))
    client.post(reverse("orders:cart_add", args=[product.pk]), {"quantity": 2})
    resp = client.post(
        reverse("orders:checkout"),
        {
            "full_name": "Buyer",
            "email": "b@e.com",
            "phone": "123",
            "shipping_address": "addr",
            "method": "card",
        },
    )
    assert resp.status_code == 302
    order = Order.objects.get(user=user)
    assert order.status == Order.Status.PAID
    assert order.total_price == Decimal("20.00")
    assert client.session.get("cart", {}) == {}
    product.refresh_from_db()
    assert product.stock == 3


@pytest.mark.django_db
def test_checkout_empty_cart_redirects(client: Client) -> None:
    user = cast(User, UserFactory())
    client.force_login(user)
    resp = client.get(reverse("orders:checkout"))
    assert resp.status_code == 302
    assert Order.objects.count() == 0


@pytest.mark.django_db
def test_order_list_shows_only_own(client: Client) -> None:
    user = cast(User, UserFactory())
    other = cast(User, UserFactory())
    OrderFactory(user=user)
    OrderFactory(user=other)
    client.force_login(user)
    resp = client.get(reverse("orders:list"))
    assert resp.status_code == 200
    assert list(resp.context["orders"]) == list(Order.objects.filter(user=user))


@pytest.mark.django_db
def test_order_detail_other_user_404(client: Client) -> None:
    user = cast(User, UserFactory())
    other = cast(User, UserFactory())
    order = cast(Order, OrderFactory(user=other))
    client.force_login(user)
    resp = client.get(reverse("orders:order_detail", args=[order.pk]))
    assert resp.status_code == 404
