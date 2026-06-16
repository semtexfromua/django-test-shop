"""Cart view tests."""
from typing import cast

import pytest
from django.test import Client
from django.urls import reverse

from products.models import Product
from products.tests.factories import ProductFactory


@pytest.mark.django_db
def test_cart_add_view(client: Client) -> None:
    product = cast(Product, ProductFactory(stock=10))
    resp = client.post(reverse("orders:cart_add", args=[product.pk]), {"quantity": 2})
    assert resp.status_code == 302
    assert client.session["cart"] == {str(product.pk): 2}


@pytest.mark.django_db
def test_cart_add_caps_at_stock(client: Client) -> None:
    product = cast(Product, ProductFactory(stock=3))
    client.post(reverse("orders:cart_add", args=[product.pk]), {"quantity": 10})
    assert client.session["cart"][str(product.pk)] == 3


@pytest.mark.django_db
def test_cart_detail_renders(client: Client) -> None:
    product = cast(Product, ProductFactory(stock=5))
    client.post(reverse("orders:cart_add", args=[product.pk]), {"quantity": 1})
    resp = client.get(reverse("orders:cart_detail"))
    assert resp.status_code == 200
    assert product.name in resp.content.decode()


@pytest.mark.django_db
def test_cart_remove_view(client: Client) -> None:
    product = cast(Product, ProductFactory(stock=5))
    client.post(reverse("orders:cart_add", args=[product.pk]), {"quantity": 1})
    client.post(reverse("orders:cart_remove", args=[product.pk]))
    assert client.session.get("cart", {}) == {}
