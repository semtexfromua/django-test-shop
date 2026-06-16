"""Тести GraphQL-аналітики."""
import json
from decimal import Decimal
from typing import Any, cast

import pytest
from django.test import Client, override_settings
from graphql import parse, validate

from config.urls import graphql_validation_rules
from gql.schema import schema
from orders.models import Order
from users.models import User
from users.tests.factories import UserFactory


def _gql(client: Client, query: str) -> Any:
    return client.post(
        "/graphql/", data=json.dumps({"query": query}), content_type="application/json"
    )


@override_settings(DEBUG=True)
def test_graphql_introspection_allowed_in_dev() -> None:
    assert graphql_validation_rules() == []  # DEBUG=True → GraphiQL працює


@override_settings(DEBUG=False)
def test_graphql_introspection_disabled_in_prod() -> None:
    rules = graphql_validation_rules()
    gs = schema.graphql_schema
    assert validate(gs, parse("{ __schema { types { name } } }"), rules)  # introspection блокується
    assert not validate(gs, parse("{ revenue }"), rules)  # звичайний запит проходить


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
def test_graphql_denied_for_anonymous() -> None:
    resp = _gql(Client(), "{ revenue }")
    body = resp.json()
    assert body.get("errors")
    assert body["data"]["revenue"] is None


@pytest.mark.django_db
def test_graphql_denied_for_non_staff() -> None:
    user = cast(User, UserFactory())
    client = Client()
    client.force_login(user)
    resp = _gql(client, "{ revenue }")
    body = resp.json()
    assert body.get("errors")
    assert body["data"]["revenue"] is None
