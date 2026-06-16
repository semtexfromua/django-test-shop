"""Сесійний кошик для веб-інтерфейсу."""
from collections.abc import Iterator
from decimal import Decimal
from typing import Any

from django.http import HttpRequest

from products.models import Product

CART_SESSION_KEY = "cart"


class Cart:
    """Кошик, що зберігається в сесії як {product_id: quantity}."""

    def __init__(self, request: HttpRequest) -> None:
        self.session = request.session
        cart = self.session.get(CART_SESSION_KEY)
        if cart is None:
            cart = self.session[CART_SESSION_KEY] = {}
        self._cart: dict[str, int] = cart

    def add(self, product: Product, quantity: int = 1, *, override: bool = False) -> None:
        pid = str(product.pk)
        if override:
            self._cart[pid] = quantity
        else:
            self._cart[pid] = self._cart.get(pid, 0) + quantity
        self.save()

    def remove(self, product: Product) -> None:
        pid = str(product.pk)
        if pid in self._cart:
            del self._cart[pid]
            self.save()

    def __iter__(self) -> Iterator[dict[str, Any]]:
        products = Product.objects.filter(pk__in=self._cart.keys())
        for product in products:
            quantity = self._cart[str(product.pk)]
            yield {
                "product": product,
                "quantity": quantity,
                "price": product.price,
                "subtotal": product.price * quantity,
            }

    def __len__(self) -> int:
        return sum(self._cart.values())

    def total(self) -> Decimal:
        products = Product.objects.filter(pk__in=self._cart.keys())
        return sum((p.price * self._cart[str(p.pk)] for p in products), Decimal("0"))

    def clear(self) -> None:
        self._cart.clear()
        self.save()

    def save(self) -> None:
        self.session.modified = True
