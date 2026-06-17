"""Order email Celery task tests (run eagerly)."""
import smtplib
from decimal import Decimal
from typing import cast
from unittest import mock

import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core import mail
from django.core.mail import EmailMultiAlternatives
from django.test import RequestFactory, override_settings

from orders.models import Order, OrderItem
from orders.tasks import send_order_email
from products.models import Product
from products.tests.factories import ProductFactory
from users.models import User
from users.tests.factories import UserFactory


def _order(user: User) -> Order:
    order = Order.objects.create(
        user=user, status=Order.Status.PAID, full_name="Buyer", email="b@e.com",
        phone="1", shipping_address="addr", total_price=Decimal("20.00"),
    )
    product = cast(Product, ProductFactory(price=Decimal("10.00"), stock=48))
    OrderItem.objects.create(order=order, product=product, quantity=2, price=Decimal("10.00"))
    return order


@pytest.mark.django_db
@override_settings(DEFAULT_FROM_EMAIL="shop@shop.test")
def test_send_order_email_customer() -> None:
    order = _order(cast(User, UserFactory()))
    send_order_email(order.pk, "customer")
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ["b@e.com"]
    assert f"#{order.pk}" in mail.outbox[0].subject


@pytest.mark.django_db
@override_settings(ADMINS=[("Admin", "admin@shop.test")])
def test_send_order_email_admin() -> None:
    order = _order(cast(User, UserFactory()))
    send_order_email(order.pk, "admin")
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ["admin@shop.test"]


def test_send_order_email_configured_to_retry_on_transient_errors() -> None:
    # transient SMTP/connection errors auto-retry with backoff (a real worker re-runs the task)
    assert send_order_email.max_retries == 5
    assert smtplib.SMTPException in send_order_email.autoretry_for
    assert OSError in send_order_email.autoretry_for
    assert send_order_email.retry_backoff


@pytest.mark.django_db
@override_settings(DEFAULT_FROM_EMAIL="shop@shop.test")
def test_send_order_email_failure_is_not_swallowed() -> None:
    # no fail_silently: a send failure propagates so Celery's autoretry catches it
    order = _order(cast(User, UserFactory()))
    with (
        mock.patch.object(
            EmailMultiAlternatives, "send", side_effect=smtplib.SMTPException("boom")
        ),
        pytest.raises(smtplib.SMTPException),
    ):
        send_order_email(order.pk, "customer")
    assert mail.outbox == []


@pytest.mark.django_db
@override_settings(ADMINS=[("Admin", "admin@shop.test")], DEFAULT_FROM_EMAIL="shop@shop.test")
def test_admin_resend_action_sends_both() -> None:
    from orders.admin import OrderAdmin

    order = _order(cast(User, UserFactory()))
    req = RequestFactory().post("/admin/")
    setattr(req, "session", {})  # noqa: B010 — minimal request plumbing for message_user
    setattr(req, "_messages", FallbackStorage(req))  # noqa: B010
    OrderAdmin(Order, AdminSite()).resend_emails(req, Order.objects.filter(pk=order.pk))
    assert len(mail.outbox) == 2  # customer + admin (eager)
