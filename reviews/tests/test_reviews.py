"""Тести відгуків (правило «лише після покупки»)."""
from decimal import Decimal
from typing import cast

import pytest
from django.test import Client
from django.urls import reverse

from orders.models import Order, OrderItem
from products.models import Product
from products.tests.factories import ProductFactory
from reviews.models import Review
from reviews.services import can_review, has_purchased
from users.models import User
from users.tests.factories import UserFactory


def _paid_order(user: User, product: Product, qty: int = 1) -> Order:
    order = Order.objects.create(
        user=user,
        status=Order.Status.PAID,
        full_name="B",
        email="b@e.com",
        phone="1",
        shipping_address="a",
        total_price=Decimal("10"),
    )
    OrderItem.objects.create(order=order, product=product, quantity=qty, price=product.price)
    return order


@pytest.mark.django_db
def test_has_purchased_true_after_paid_order() -> None:
    user = cast(User, UserFactory())
    product = cast(Product, ProductFactory())
    _paid_order(user, product)
    assert has_purchased(user, product) is True


@pytest.mark.django_db
def test_has_purchased_false_without_order() -> None:
    user = cast(User, UserFactory())
    product = cast(Product, ProductFactory())
    assert has_purchased(user, product) is False


@pytest.mark.django_db
def test_can_review_false_after_existing_review() -> None:
    user = cast(User, UserFactory())
    product = cast(Product, ProductFactory())
    _paid_order(user, product)
    Review.objects.create(product=product, user=user, rating=5, comment="x")
    assert can_review(user, product) is False


@pytest.mark.django_db
def test_review_create_blocked_for_non_purchaser(client: Client) -> None:
    user = cast(User, UserFactory())
    client.force_login(user)
    product = cast(Product, ProductFactory())
    resp = client.post(
        reverse("reviews:create", args=[product.slug]), {"rating": 5, "comment": "nice"}
    )
    assert resp.status_code == 302
    assert Review.objects.count() == 0


@pytest.mark.django_db
def test_review_create_succeeds_for_purchaser(client: Client) -> None:
    user = cast(User, UserFactory())
    client.force_login(user)
    product = cast(Product, ProductFactory())
    _paid_order(user, product)
    resp = client.post(
        reverse("reviews:create", args=[product.slug]), {"rating": 4, "comment": "good"}
    )
    assert resp.status_code == 302
    review = Review.objects.get(product=product, user=user)
    assert review.rating == 4


@pytest.mark.django_db
def test_review_create_blocked_for_anonymous(client: Client) -> None:
    product = cast(Product, ProductFactory())
    resp = client.post(
        reverse("reviews:create", args=[product.slug]), {"rating": 5, "comment": "x"}
    )
    assert resp.status_code == 302
    assert reverse("users:login") in resp["Location"]
    assert Review.objects.count() == 0


@pytest.mark.django_db
def test_review_create_rejects_out_of_range_rating(client: Client) -> None:
    user = cast(User, UserFactory())
    client.force_login(user)
    product = cast(Product, ProductFactory())
    _paid_order(user, product)
    resp = client.post(
        reverse("reviews:create", args=[product.slug]), {"rating": 99, "comment": "x"}
    )
    assert resp.status_code == 200  # форма невалідна → перерендер
    assert Review.objects.count() == 0


@pytest.mark.django_db
def test_pending_order_does_not_grant_review() -> None:
    user = cast(User, UserFactory())
    product = cast(Product, ProductFactory())
    order = Order.objects.create(
        user=user,
        status=Order.Status.PENDING,
        full_name="B",
        email="b@e.com",
        phone="1",
        shipping_address="a",
        total_price=Decimal("10"),
    )
    OrderItem.objects.create(order=order, product=product, quantity=1, price=product.price)
    assert has_purchased(user, product) is False
    assert can_review(user, product) is False


@pytest.mark.django_db
def test_view_level_duplicate_review_blocked(client: Client) -> None:
    user = cast(User, UserFactory())
    client.force_login(user)
    product = cast(Product, ProductFactory())
    _paid_order(user, product)
    client.post(reverse("reviews:create", args=[product.slug]), {"rating": 5, "comment": "1"})
    client.post(reverse("reviews:create", args=[product.slug]), {"rating": 3, "comment": "2"})
    assert Review.objects.filter(product=product, user=user).count() == 1


@pytest.mark.django_db
def test_reviews_show_on_product_detail(client: Client) -> None:
    user = cast(User, UserFactory())
    product = cast(Product, ProductFactory())
    Review.objects.create(product=product, user=user, rating=5, comment="Excellent brew")
    resp = client.get(product.get_absolute_url())
    assert resp.status_code == 200
    assert "Excellent brew" in resp.content.decode()
    assert resp.context["avg_rating"] == 5.0
