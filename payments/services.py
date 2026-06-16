"""Mock payment processing."""
from orders.models import Order

from .models import Payment


def process_payment(order: Order, method: str) -> Payment:
    """Mock: payment always succeeds; marks the order as paid."""
    payment = Payment.objects.create(
        order=order,
        method=method,
        amount=order.total_price,
        status=Payment.Status.PAID,
        transaction_id=f"mock-{order.pk}",
    )
    order.status = Order.Status.PAID
    order.save(update_fields=["status"])
    return payment
