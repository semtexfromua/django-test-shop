"""Агрегації для адмін-аналітики."""
from decimal import Decimal
from typing import Any

from django.db.models import Count, Sum

from .models import Order, OrderItem

_REVENUE_STATUSES = (Order.Status.PAID, Order.Status.SHIPPED, Order.Status.DELIVERED)


def total_revenue() -> Decimal:
    agg = Order.objects.filter(status__in=_REVENUE_STATUSES).aggregate(total=Sum("total_price"))
    return agg["total"] or Decimal("0")


def order_count() -> int:
    return Order.objects.count()


def orders_by_status() -> dict[str, int]:
    rows = Order.objects.values("status").annotate(n=Count("id"))
    return {row["status"]: row["n"] for row in rows}


def top_products(limit: int = 5) -> list[dict[str, Any]]:
    limit = max(0, min(limit, 100))
    return list(
        OrderItem.objects.values("product_id", "product__name")
        .annotate(sold=Sum("quantity"))
        .order_by("-sold")[:limit]
    )
