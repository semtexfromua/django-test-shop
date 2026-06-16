"""GraphQL schema: shop analytics (staff-only access)."""
from typing import Any

import graphene
from graphql import GraphQLError

from orders import analytics


def _require_staff(info: Any) -> None:
    user = info.context.user
    if not user.is_authenticated or not user.is_staff:
        raise GraphQLError("Доступ лише для персоналу.")


class TopProduct(graphene.ObjectType):
    name = graphene.String()
    sold = graphene.Int()


class Query(graphene.ObjectType):
    revenue = graphene.Float()
    order_count = graphene.Int()
    top_products = graphene.List(TopProduct, limit=graphene.Int(default_value=5))

    def resolve_revenue(root: Any, info: Any) -> float:
        _require_staff(info)
        return float(analytics.total_revenue())

    def resolve_order_count(root: Any, info: Any) -> int:
        _require_staff(info)
        return analytics.order_count()

    def resolve_top_products(root: Any, info: Any, limit: int) -> list[TopProduct]:
        _require_staff(info)
        return [
            TopProduct(name=row["product__name"], sold=row["sold"])
            for row in analytics.top_products(limit)
        ]


schema = graphene.Schema(query=Query)
