from django.http import HttpRequest

from .cart import Cart


def cart_count(request: HttpRequest) -> dict[str, int]:
    """Expose the session cart item count for the header badge in base.html."""
    return {"cart_count": len(Cart(request))}
