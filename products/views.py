"""В'юхи каталогу."""
from decimal import Decimal, InvalidOperation
from typing import Any

from django.db.models import Q, QuerySet
from django.views.generic import DetailView, ListView

from .models import Category, Product

SORT_OPTIONS = {"price", "-price", "-created_at"}


def _parse_decimal(value: str | None) -> Decimal | None:
    if not value:
        return None
    try:
        result = Decimal(value)
    except (InvalidOperation, TypeError):
        return None
    # NaN/Infinity парсяться як Decimal, але валять filter(price__gte=...) → 500.
    return result if result.is_finite() else None


class ProductListView(ListView):
    model = Product
    template_name = "products/product_list.html"
    context_object_name = "products"
    paginate_by = 12

    def get_queryset(self) -> QuerySet[Product]:
        qs = Product.objects.active().select_related("category")
        params = self.request.GET
        if category := params.get("category"):
            qs = qs.filter(category__slug=category)
        if (min_price := _parse_decimal(params.get("min_price"))) is not None:
            qs = qs.filter(price__gte=min_price)
        if (max_price := _parse_decimal(params.get("max_price"))) is not None:
            qs = qs.filter(price__lte=max_price)
        if q := params.get("q"):
            qs = qs.filter(Q(name__icontains=q) | Q(description__icontains=q))
        sort = params.get("sort")
        if sort in SORT_OPTIONS:
            qs = qs.order_by(sort)
        return qs

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        ctx = super().get_context_data(**kwargs)
        ctx["categories"] = Category.objects.all()
        ctx["current"] = self.request.GET
        params = self.request.GET.copy()
        params.pop("page", None)
        ctx["querystring"] = params.urlencode()
        return ctx


class ProductDetailView(DetailView):
    model = Product
    template_name = "products/product_detail.html"
    context_object_name = "product"

    def get_queryset(self) -> QuerySet[Product]:
        return Product.objects.active().select_related("category")
