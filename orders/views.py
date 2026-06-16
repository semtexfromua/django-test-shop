"""В'юхи кошика, оформлення та замовлень."""
from typing import Any, cast

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, FormView, ListView

from payments.services import process_payment
from products.models import Product
from users.models import User

from .cart import Cart
from .forms import OrderForm
from .models import Order
from .services import InsufficientStock, OrderContact, create_order


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


class CheckoutView(LoginRequiredMixin, FormView):
    template_name = "orders/checkout.html"
    form_class = OrderForm

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if len(Cart(request)) == 0:
            return redirect("orders:cart_detail")
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        ctx = super().get_context_data(**kwargs)
        ctx["cart"] = Cart(self.request)
        return ctx

    def form_valid(self, form: OrderForm) -> HttpResponse:
        cart = Cart(self.request)
        items = [(item["product"], item["quantity"]) for item in cart]
        if not items:
            messages.error(self.request, "Кошик порожній.")
            return redirect("orders:cart_detail")
        contact = OrderContact(
            full_name=form.cleaned_data["full_name"],
            email=form.cleaned_data["email"],
            phone=form.cleaned_data["phone"],
            shipping_address=form.cleaned_data["shipping_address"],
        )
        try:
            with transaction.atomic():
                order = create_order(cast(User, self.request.user), items, contact)
                process_payment(order, form.cleaned_data["method"])
        except InsufficientStock as exc:
            messages.error(self.request, str(exc))
            return redirect("orders:cart_detail")
        cart.clear()
        messages.success(self.request, f"Замовлення #{order.pk} оформлено й оплачено.")
        return redirect("orders:order_detail", pk=order.pk)


class OrderListView(LoginRequiredMixin, ListView):
    template_name = "orders/order_list.html"
    context_object_name = "orders"

    def get_queryset(self) -> QuerySet[Order]:
        return Order.objects.filter(user=cast(User, self.request.user))


class OrderDetailView(LoginRequiredMixin, DetailView):
    template_name = "orders/order_detail.html"
    context_object_name = "order"

    def get_queryset(self) -> QuerySet[Order]:
        return Order.objects.filter(user=cast(User, self.request.user)).prefetch_related(
            "items__product"
        )
