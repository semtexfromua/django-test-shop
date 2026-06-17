from decimal import Decimal
from typing import Any, cast

import pytest
from django.core import mail
from django.test import override_settings

from orders.models import Order, OrderItem
from orders.services import InsufficientStock, OrderContact, create_order
from products.models import Product
from products.tests.factories import ProductFactory
from users.models import User
from users.tests.factories import UserFactory

CONTACT = OrderContact(full_name="Buyer", email="b@e.com", phone="123", shipping_address="addr")


@pytest.mark.django_db
def test_create_order_success() -> None:
    user = cast(User, UserFactory())
    p1 = cast(Product, ProductFactory(price=Decimal("10.00"), stock=5))
    p2 = cast(Product, ProductFactory(price=Decimal("4.00"), stock=5))
    order = create_order(user, [(p1, 2), (p2, 1)], CONTACT)
    assert order.status == Order.Status.PENDING
    assert order.total_price == Decimal("24.00")
    assert order.items.count() == 2
    p1.refresh_from_db()
    p2.refresh_from_db()
    assert p1.stock == 3
    assert p2.stock == 4


@pytest.mark.django_db
def test_create_order_price_snapshot() -> None:
    user = cast(User, UserFactory())
    p = cast(Product, ProductFactory(price=Decimal("10.00"), stock=5))
    order = create_order(user, [(p, 1)], CONTACT)
    item = cast(OrderItem, order.items.first())
    assert item.price == Decimal("10.00")
    p.price = Decimal("99.00")
    p.save()
    item.refresh_from_db()
    assert item.price == Decimal("10.00")


@pytest.mark.django_db
def test_create_order_overselling_rolls_back() -> None:
    user = cast(User, UserFactory())
    p = cast(Product, ProductFactory(price=Decimal("10.00"), stock=2))
    with pytest.raises(InsufficientStock):
        create_order(user, [(p, 5)], CONTACT)
    assert Order.objects.count() == 0
    p.refresh_from_db()
    assert p.stock == 2


@pytest.mark.django_db
@override_settings(ADMINS=[("Admin", "admin@shop.test")], DEFAULT_FROM_EMAIL="shop@shop.test")
def test_create_order_emails_customer_and_admin(django_capture_on_commit_callbacks: Any) -> None:
    user = cast(User, UserFactory())
    p = cast(Product, ProductFactory(price=Decimal("10.00"), stock=5))
    with django_capture_on_commit_callbacks(execute=True):
        order = create_order(user, [(p, 2)], CONTACT)
    assert len(mail.outbox) == 2
    customer, admin = mail.outbox
    assert customer.to == [CONTACT.email]
    assert customer.from_email == "shop@shop.test"
    assert f"#{order.pk}" in customer.subject
    assert f"#{order.pk}" in customer.body and "20.00" in customer.body
    assert admin.to == ["admin@shop.test"]
    assert f"#{order.pk}" in admin.subject
    assert CONTACT.email in admin.body


@pytest.mark.django_db
@override_settings(ADMINS=[])
def test_order_email_skipped_without_admins(django_capture_on_commit_callbacks: Any) -> None:
    user = cast(User, UserFactory())
    p = cast(Product, ProductFactory(price=Decimal("10.00"), stock=5))
    with django_capture_on_commit_callbacks(execute=True):
        create_order(user, [(p, 1)], CONTACT)
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == [CONTACT.email]


@pytest.mark.django_db
def test_create_order_rejects_inactive_product() -> None:
    user = cast(User, UserFactory())
    p = cast(Product, ProductFactory(price=Decimal("10.00"), stock=5, is_active=False))
    with pytest.raises(InsufficientStock):
        create_order(user, [(p, 1)], CONTACT)
    assert Order.objects.count() == 0
