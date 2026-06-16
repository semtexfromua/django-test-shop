"""factory_boy order factories."""
from decimal import Decimal

import factory
from factory.django import DjangoModelFactory

from orders.models import Order, OrderItem
from products.tests.factories import ProductFactory
from users.tests.factories import UserFactory


class OrderFactory(DjangoModelFactory):
    class Meta:
        model = Order

    user = factory.SubFactory(UserFactory)
    full_name = "Test Buyer"
    email = "buyer@example.com"
    phone = "+380000000000"
    shipping_address = "Test address 1"


class OrderItemFactory(DjangoModelFactory):
    class Meta:
        model = OrderItem

    order = factory.SubFactory(OrderFactory)
    product = factory.SubFactory(ProductFactory)
    quantity = 1
    price = Decimal("9.99")
