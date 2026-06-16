"""Тести сесійного кошика."""
from decimal import Decimal
from typing import cast

import pytest
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpRequest, HttpResponse
from django.test import RequestFactory

from orders.cart import Cart
from products.models import Product
from products.tests.factories import ProductFactory


@pytest.fixture
def http_request() -> HttpRequest:
    request = RequestFactory().get("/")
    middleware = SessionMiddleware(lambda req: HttpResponse())
    middleware.process_request(request)
    request.session.save()
    return request


@pytest.mark.django_db
def test_cart_add_and_total(http_request: HttpRequest) -> None:
    p1 = cast(Product, ProductFactory(price=Decimal("10.00")))
    p2 = cast(Product, ProductFactory(price=Decimal("5.00")))
    cart = Cart(http_request)
    cart.add(p1, 2)
    cart.add(p2, 1)
    assert len(cart) == 3
    assert cart.total() == Decimal("25.00")


@pytest.mark.django_db
def test_cart_override_and_remove(http_request: HttpRequest) -> None:
    product = cast(Product, ProductFactory(price=Decimal("10.00")))
    cart = Cart(http_request)
    cart.add(product, 1)
    cart.add(product, 5, override=True)
    assert len(cart) == 5
    cart.remove(product)
    assert len(cart) == 0


@pytest.mark.django_db
def test_cart_iter_yields_items(http_request: HttpRequest) -> None:
    product = cast(Product, ProductFactory(price=Decimal("10.00")))
    cart = Cart(http_request)
    cart.add(product, 2)
    items = list(cart)
    assert len(items) == 1
    assert items[0]["product"] == product
    assert items[0]["subtotal"] == Decimal("20.00")


@pytest.mark.django_db
def test_cart_clear(http_request: HttpRequest) -> None:
    product = cast(Product, ProductFactory())
    cart = Cart(http_request)
    cart.add(product, 1)
    cart.clear()
    assert len(cart) == 0
