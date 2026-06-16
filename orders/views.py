"""В'юхи кошика."""
from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from products.models import Product

from .cart import Cart


def _quantity(request: HttpRequest, default: int = 1) -> int:
    try:
        return int(request.POST.get("quantity", default))
    except (TypeError, ValueError):
        return default


def cart_detail(request: HttpRequest) -> HttpResponse:
    return render(request, "orders/cart.html", {"cart": Cart(request)})


@require_POST
def cart_add(request: HttpRequest, product_id: int) -> HttpResponse:
    product = get_object_or_404(Product.objects.active(), pk=product_id)
    cart = Cart(request)
    quantity = max(1, _quantity(request))
    if quantity > product.stock:
        quantity = product.stock
        messages.warning(request, f"Доступно лише {product.stock} шт.")
    if quantity > 0:
        cart.add(product, quantity)
        messages.success(request, f"«{product.name}» додано в кошик.")
    else:
        messages.error(request, "Товару немає в наявності.")
    return redirect("orders:cart_detail")


@require_POST
def cart_update(request: HttpRequest, product_id: int) -> HttpResponse:
    product = get_object_or_404(Product.objects.active(), pk=product_id)
    cart = Cart(request)
    quantity = max(1, _quantity(request))
    if product.stock:
        cart.add(product, min(quantity, product.stock), override=True)
    return redirect("orders:cart_detail")


@require_POST
def cart_remove(request: HttpRequest, product_id: int) -> HttpResponse:
    product = get_object_or_404(Product, pk=product_id)
    Cart(request).remove(product)
    return redirect("orders:cart_detail")
