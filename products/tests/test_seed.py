"""Тест seed-команди каталогу."""
import pytest
from django.core.management import call_command

from products.models import Category, Product


@pytest.mark.django_db
def test_seed_creates_catalog() -> None:
    call_command("seed_catalog")
    assert Category.objects.count() == 5
    assert Product.objects.count() == 12


@pytest.mark.django_db
def test_seed_is_idempotent() -> None:
    call_command("seed_catalog")
    call_command("seed_catalog")
    assert Category.objects.count() == 5
    assert Product.objects.count() == 12
