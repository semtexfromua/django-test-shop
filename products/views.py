from decimal import Decimal, InvalidOperation
from typing import Any, cast

from django.db.models import Avg, IntegerField, OuterRef, Q, QuerySet, Subquery, Sum
from django.db.models.functions import Coalesce
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
    # NaN/Infinity parse as Decimal but break filter(price__gte=...) → 500.
    return result if result.is_finite() else None


class ProductListView(ListView):
    """Catalog: active products with filters (category/price), search, sorting, pagination."""

    model = Product
    template_name = "products/product_list.html"
    context_object_name = "products"
    paginate_by = 12

    def get_queryset(self) -> QuerySet[Product]:
        # avg_rating for the card rating block; Avg over the reviews join is invariant to
        # row duplication, so it stays correct even alongside other annotations.
        qs = (
            Product.objects.active()
            .select_related("category")
            .annotate(avg_rating=Avg("reviews__rating"))
        )
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
        if sort == "popularity":
            # sold via Subquery so the reviews join above can't inflate the sum (JOIN inflation).
            # local import keeps products from importing orders at module level (cycle).
            from orders.models import OrderItem

            sold = Subquery(
                OrderItem.objects.filter(product=OuterRef("pk"))
                .values("product")
                .annotate(total=Sum("quantity"))
                .values("total"),
                output_field=IntegerField(),
            )
            qs = qs.annotate(_sold=Coalesce(sold, 0)).order_by("-_sold")
        elif sort in SORT_OPTIONS:
            qs = qs.order_by(sort)
        else:
            qs = qs.order_by("-created_at")  # explicit: the Avg annotate drops implicit Meta order
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

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        ctx = super().get_context_data(**kwargs)
        product = cast(Product, self.object)
        # reverse accessor `reviews` (from the reviews app) — no import, to avoid a cycle
        reviews = product.reviews.select_related("user")
        ctx["reviews"] = reviews
        ctx["avg_rating"] = reviews.aggregate(avg=Avg("rating"))["avg"]
        return ctx
