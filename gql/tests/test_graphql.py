"""Тести GraphQL-аналітики."""
import json
from decimal import Decimal
from typing import Any, cast

import pytest
from django.test import Client

from orders.models import Order
from users.models import User
from users.tests.factories import UserFactory


def _gql(client: Client, query: str) -> Any:
    return client.post(
        "/graphql/", data=json.dumps({"query": query}), content_type="application/json"
    )


@pytest.mark.django_db
def test_graphql_revenue_for_staff() -> None:
    staff = cast(User, UserFactory(is_staff=True))
    client = Client()
    client.force_login(staff)
    Order.objects.create(
        user=staff,
        status=Order.Status.PAID,
        full_name="b",
        email="b@e.com",
        phone="1",
        shipping_address="a",
        total_price=Decimal("42"),
    )
    resp = _gql(client, "{ revenue orderCount }")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["revenue"] == 42.0
    assert data["orderCount"] == 1


@pytest.mark.django_db
def test_graphql_denied_for_non_staff() -> None:
    user = cast(User, UserFactory())
    client = Client()
    client.force_login(user)
    resp = _gql(client, "{ revenue }")
    body = resp.json()
    assert body.get("errors")
    assert body["data"]["revenue"] is None
