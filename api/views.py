"""DRF viewsets та APIViews."""
from typing import Any, cast

from django.db import transaction
from django.db.models import Avg, QuerySet
from django.shortcuts import get_object_or_404
from rest_framework import generics, mixins, status, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from orders.models import CartItem, Order
from orders.services import InsufficientStock, OrderContact, create_order
from payments.services import process_payment
from products.models import Product
from reviews.models import Review
from reviews.services import can_review
from users.models import User

from .permissions import IsOwner
from .serializers import (
    CartItemSerializer,
    OrderSerializer,
    ProductSerializer,
    RegisterSerializer,
    ReviewSerializer,
)


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]
    filterset_fields = ["category"]
    search_fields = ["name", "description"]
    ordering_fields = ["price", "created_at"]

    def get_queryset(self) -> QuerySet[Product]:
        return (
            Product.objects.active()
            .select_related("category")
            .annotate(avg_rating=Avg("reviews__rating"))
        )


class ProductReviewsView(generics.ListCreateAPIView):
    serializer_class = ReviewSerializer

    def get_permissions(self) -> list[Any]:
        return [IsAuthenticated()] if self.request.method == "POST" else [AllowAny()]

    def _product(self) -> Product:
        return get_object_or_404(Product.objects.active(), pk=self.kwargs["pk"])

    def get_queryset(self) -> QuerySet[Review]:
        return Review.objects.filter(product=self._product()).select_related("user")

    def perform_create(self, serializer: Any) -> None:
        product = self._product()
        user = cast(User, self.request.user)
        if not can_review(user, product):
            raise PermissionDenied("Відгук можна лишити лише після покупки (один раз).")
        serializer.save(user=user, product=product)


class CartItemViewSet(viewsets.ModelViewSet):
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[CartItem]:
        return CartItem.objects.filter(user=cast(User, self.request.user)).select_related("product")

    def perform_create(self, serializer: Any) -> None:
        item, _ = CartItem.objects.update_or_create(
            user=cast(User, self.request.user),
            product=serializer.validated_data["product"],
            defaults={"quantity": serializer.validated_data.get("quantity", 1)},
        )
        serializer.instance = item

    def perform_update(self, serializer: Any) -> None:
        # на існуючій позиції змінюємо лише кількість; товар фіксований (інакше unique 500)
        serializer.save(product=serializer.instance.product)


class OrderViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    # без update/destroy: оплачене замовлення не редагують/видаляють через API
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self) -> QuerySet[Order]:
        user = cast(User, self.request.user)
        return Order.objects.filter(user=user).prefetch_related("items__product")

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        user = cast(User, request.user)
        cart_items = list(CartItem.objects.filter(user=user).select_related("product"))
        if not cart_items:
            return Response({"detail": "Кошик порожній."}, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        items = [(ci.product, ci.quantity) for ci in cart_items]
        contact = OrderContact(
            full_name=serializer.validated_data["full_name"],
            email=serializer.validated_data["email"],
            phone=serializer.validated_data["phone"],
            shipping_address=serializer.validated_data["shipping_address"],
        )
        try:
            with transaction.atomic():
                order = create_order(user, items, contact)
                process_payment(order, request.data.get("method", "card"))
        except InsufficientStock as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        CartItem.objects.filter(user=user).delete()
        return Response(self.get_serializer(order).data, status=status.HTTP_201_CREATED)


class RegisterAPIView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
