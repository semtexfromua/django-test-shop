"""factory_boy factories for catalog tests."""
from decimal import Decimal

import factory
from factory.django import DjangoModelFactory

from products.models import Category, Product


class CategoryFactory(DjangoModelFactory):
    class Meta:
        model = Category

    name = factory.Sequence(lambda n: f"Category {n}")


class ProductFactory(DjangoModelFactory):
    class Meta:
        model = Product

    name = factory.Sequence(lambda n: f"Product {n}")
    description = "Test product"
    price = Decimal("9.99")
    category = factory.SubFactory(CategoryFactory)
    stock = 10
    is_active = True
