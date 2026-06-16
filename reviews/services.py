"""Review permission logic."""
from orders.models import Order, OrderItem
from products.models import Product
from users.models import User

from .models import Review

_PURCHASED = (Order.Status.PAID, Order.Status.SHIPPED, Order.Status.DELIVERED)


def has_purchased(user: User, product: Product) -> bool:
    return OrderItem.objects.filter(
        order__user=user, order__status__in=_PURCHASED, product=product
    ).exists()


def can_review(user: User, product: Product) -> bool:
    """Allowed if the user purchased the product and hasn't reviewed it yet."""
    if not has_purchased(user, product):
        return False
    return not Review.objects.filter(product=product, user=user).exists()
