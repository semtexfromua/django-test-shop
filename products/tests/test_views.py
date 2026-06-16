"""Тести в'юх каталогу."""
from decimal import Decimal
from typing import Any, cast

import pytest
from django.test import Client, RequestFactory
from django.urls import reverse

from products.models import Category
from products.tests.factories import CategoryFactory, ProductFactory
from products.views import ProductListView


@pytest.mark.django_db
def test_catalog_lists_only_active(client: Client) -> None:
    ProductFactory(name="Visible", is_active=True)
    ProductFactory(name="Hidden", is_active=False)
    resp = client.get(reverse("products:list"))
    assert resp.status_code == 200
    names = [p.name for p in resp.context["products"]]
    assert "Visible" in names
    assert "Hidden" not in names


@pytest.mark.django_db
def test_catalog_pagination(client: Client) -> None:
    ProductFactory.create_batch(15)
    resp = client.get(reverse("products:list"))
    assert len(resp.context["products"]) == 12


@pytest.mark.django_db
def test_catalog_filter_by_category(client: Client) -> None:
    cat = cast(Category, CategoryFactory(name="Hops"))
    other = CategoryFactory(name="Malts")
    ProductFactory(name="InHops", category=cat)
    ProductFactory(name="InMalts", category=other)
    resp = client.get(reverse("products:list"), {"category": cat.slug})
    names = [p.name for p in resp.context["products"]]
    assert names == ["InHops"]


@pytest.mark.django_db
def test_catalog_filter_by_price_range(client: Client) -> None:
    ProductFactory(name="Cheap", price=Decimal("5"))
    ProductFactory(name="Pricey", price=Decimal("50"))
    resp = client.get(reverse("products:list"), {"min_price": "10", "max_price": "100"})
    names = [p.name for p in resp.context["products"]]
    assert names == ["Pricey"]


@pytest.mark.django_db
def test_catalog_search_name_and_description(client: Client) -> None:
    ProductFactory(name="Cascade Hops", description="citrus aroma")
    ProductFactory(name="Pilsner Malt", description="base malt")
    by_name = client.get(reverse("products:list"), {"q": "cascade"})
    assert [p.name for p in by_name.context["products"]] == ["Cascade Hops"]
    by_desc = client.get(reverse("products:list"), {"q": "base malt"})
    assert [p.name for p in by_desc.context["products"]] == ["Pilsner Malt"]


@pytest.mark.django_db
def test_catalog_sort_by_price(client: Client) -> None:
    ProductFactory(name="B", price=Decimal("20"))
    ProductFactory(name="A", price=Decimal("10"))
    resp = client.get(reverse("products:list"), {"sort": "price"})
    prices = [p.price for p in resp.context["products"]]
    assert prices == sorted(prices)


@pytest.mark.django_db
def test_catalog_queryset_avoids_n_plus_one(django_assert_num_queries: Any) -> None:
    cat = CategoryFactory()
    ProductFactory.create_batch(3, category=cat)
    view = ProductListView()
    view.request = RequestFactory().get("/")
    with django_assert_num_queries(1):
        products = list(view.get_queryset())
        _ = [p.category.name for p in products]
    assert len(products) == 3
