"""Тести REST API."""
from decimal import Decimal
from typing import cast

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from orders.models import CartItem, Order, OrderItem
from products.models import Product
from products.tests.factories import ProductFactory
from reviews.models import Review
from users.models import User
from users.tests.factories import UserFactory


@pytest.fixture
def api() -> APIClient:
    return APIClient()


@pytest.mark.django_db
def test_products_list_public(api: APIClient) -> None:
    ProductFactory.create_batch(3)
    resp = api.get(reverse("api:product-list"))
    assert resp.status_code == 200
    assert resp.data["count"] == 3


@pytest.mark.django_db
def test_products_write_not_allowed(api: APIClient) -> None:
    resp = api.post(reverse("api:product-list"), {"name": "x"})
    assert resp.status_code == 405  # read-only viewset


@pytest.mark.django_db
def test_register_then_login_returns_jwt(api: APIClient) -> None:
    reg = api.post(
        reverse("api:register"),
        {"username": "u1", "email": "u1@e.com", "password": "Br3wMaster!99"},
    )
    assert reg.status_code == 201
    login = api.post(
        reverse("api:token_obtain_pair"), {"username": "u1", "password": "Br3wMaster!99"}
    )
    assert login.status_code == 200
    assert "access" in login.data
    assert "refresh" in login.data


@pytest.mark.django_db
def test_orders_require_auth(api: APIClient) -> None:
    assert api.get(reverse("api:order-list")).status_code == 401


@pytest.mark.django_db
def test_cart_and_order_flow(api: APIClient) -> None:
    user = cast(User, UserFactory())
    api.force_authenticate(user=user)
    product = cast(Product, ProductFactory(price=Decimal("10.00"), stock=5))
    add = api.post(reverse("api:cart-list"), {"product": product.pk, "quantity": 2})
    assert add.status_code == 201
    assert CartItem.objects.filter(user=user).count() == 1
    order_resp = api.post(
        reverse("api:order-list"),
        {
            "full_name": "B",
            "email": "b@e.com",
            "phone": "1",
            "shipping_address": "a",
            "method": "card",
        },
    )
    assert order_resp.status_code == 201
    order = Order.objects.get(user=user)
    assert order.status == Order.Status.PAID
    assert order.total_price == Decimal("20.00")
    assert CartItem.objects.filter(user=user).count() == 0
    product.refresh_from_db()
    assert product.stock == 3


@pytest.mark.django_db
def test_orders_owner_isolation(api: APIClient) -> None:
    owner = cast(User, UserFactory())
    other = cast(User, UserFactory())
    order = Order.objects.create(
        user=owner,
        status=Order.Status.PAID,
        full_name="o",
        email="o@e.com",
        phone="1",
        shipping_address="a",
        total_price=Decimal("1"),
    )
    api.force_authenticate(user=other)
    assert api.get(reverse("api:order-detail", args=[order.pk])).status_code == 404


@pytest.mark.django_db
def test_order_update_delete_not_allowed(api: APIClient) -> None:
    user = cast(User, UserFactory())
    api.force_authenticate(user=user)
    order = Order.objects.create(
        user=user,
        status=Order.Status.PAID,
        full_name="o",
        email="o@e.com",
        phone="1",
        shipping_address="a",
        total_price=Decimal("1"),
    )
    url = reverse("api:order-detail", args=[order.pk])
    assert api.patch(url, {"phone": "x"}).status_code == 405
    assert api.delete(url).status_code == 405


@pytest.mark.django_db
def test_cart_update_product_swap_no_500(api: APIClient) -> None:
    user = cast(User, UserFactory())
    api.force_authenticate(user=user)
    p1 = cast(Product, ProductFactory(stock=5))
    p2 = cast(Product, ProductFactory(stock=5))
    item1 = CartItem.objects.create(user=user, product=p1, quantity=1)
    CartItem.objects.create(user=user, product=p2, quantity=1)
    resp = api.patch(
        reverse("api:cart-detail", args=[item1.pk]), {"product": p2.pk, "quantity": 3}
    )
    assert resp.status_code == 200
    item1.refresh_from_db()
    assert item1.product_id == p1.pk  # товар не змінився
    assert item1.quantity == 3


@pytest.mark.django_db
def test_api_order_insufficient_stock_rolls_back(api: APIClient) -> None:
    from payments.models import Payment

    user = cast(User, UserFactory())
    api.force_authenticate(user=user)
    product = cast(Product, ProductFactory(price=Decimal("10.00"), stock=1))
    CartItem.objects.create(user=user, product=product, quantity=5)
    resp = api.post(
        reverse("api:order-list"),
        {
            "full_name": "B",
            "email": "b@e.com",
            "phone": "1",
            "shipping_address": "a",
            "method": "card",
        },
    )
    assert resp.status_code == 400
    assert Order.objects.count() == 0
    assert Payment.objects.count() == 0
    assert CartItem.objects.filter(user=user).count() == 1  # кошик не очищено
    product.refresh_from_db()
    assert product.stock == 1


@pytest.mark.django_db
def test_cart_rejects_zero_quantity(api: APIClient) -> None:
    user = cast(User, UserFactory())
    api.force_authenticate(user=user)
    product = cast(Product, ProductFactory(stock=5))
    resp = api.post(reverse("api:cart-list"), {"product": product.pk, "quantity": 0})
    assert resp.status_code == 400


@pytest.mark.django_db
def test_cart_owner_isolation(api: APIClient) -> None:
    owner = cast(User, UserFactory())
    other = cast(User, UserFactory())
    product = cast(Product, ProductFactory(stock=5))
    item = CartItem.objects.create(user=owner, product=product, quantity=1)
    api.force_authenticate(user=other)
    assert api.get(reverse("api:cart-detail", args=[item.pk])).status_code == 404


@pytest.mark.django_db
def test_review_api_blocked_for_non_purchaser(api: APIClient) -> None:
    user = cast(User, UserFactory())
    api.force_authenticate(user=user)
    product = cast(Product, ProductFactory())
    resp = api.post(
        reverse("api:product-reviews", args=[product.pk]), {"rating": 5, "comment": "x"}
    )
    assert resp.status_code == 403


@pytest.mark.django_db
def test_api_order_by_sold_not_inflated_by_reviews(api: APIClient) -> None:
    buyer = cast(User, UserFactory())
    bestseller = cast(Product, ProductFactory(name="Bestseller"))
    reviewed = cast(Product, ProductFactory(name="Reviewed"))
    order = Order.objects.create(
        user=buyer,
        status=Order.Status.PAID,
        full_name="b",
        email="b@e.com",
        phone="1",
        shipping_address="a",
        total_price=Decimal("1"),
    )
    OrderItem.objects.create(order=order, product=bestseller, quantity=10, price=Decimal("1"))
    OrderItem.objects.create(order=order, product=reviewed, quantity=4, price=Decimal("1"))
    for _ in range(3):
        Review.objects.create(
            product=reviewed, user=cast(User, UserFactory()), rating=5, comment="x"
        )
    resp = api.get(reverse("api:product-list"), {"ordering": "-sold"})
    names = [p["name"] for p in resp.data["results"]]
    assert names.index("Bestseller") < names.index("Reviewed")


@pytest.mark.django_db
def test_old_refresh_token_blacklisted_after_rotation(api: APIClient) -> None:
    api.post(
        reverse("api:register"),
        {"username": "rot", "email": "rot@e.com", "password": "Br3wMaster!99"},
    )
    login = api.post(
        reverse("api:token_obtain_pair"), {"username": "rot", "password": "Br3wMaster!99"}
    )
    old_refresh = login.data["refresh"]
    rotated = api.post(reverse("api:token_refresh"), {"refresh": old_refresh})
    assert rotated.status_code == 200
    # повторне використання старого refresh після ротації — заборонено (replay)
    replay = api.post(reverse("api:token_refresh"), {"refresh": old_refresh})
    assert replay.status_code == 401


@pytest.mark.django_db
def test_schema_and_docs(api: APIClient) -> None:
    assert api.get(reverse("api:schema")).status_code == 200
    assert api.get(reverse("api:docs")).status_code == 200


@pytest.mark.django_db
def test_register_rejects_duplicate_email(api: APIClient) -> None:
    UserFactory(email="dup@e.com")
    resp = api.post(
        reverse("api:register"),
        {"username": "newbie", "email": "DUP@e.com", "password": "Br3wMaster!99"},
    )
    assert resp.status_code == 400
    assert "email" in resp.data


@pytest.mark.django_db
def test_register_requires_email(api: APIClient) -> None:
    resp = api.post(
        reverse("api:register"), {"username": "noemail", "password": "Br3wMaster!99"}
    )
    assert resp.status_code == 400
    assert "email" in resp.data
