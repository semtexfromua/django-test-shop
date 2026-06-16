"""DRF serializers."""
from typing import Any

from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from orders.models import CartItem, Order, OrderItem
from products.models import Product
from reviews.models import Review
from users.models import User


class ProductSerializer(serializers.ModelSerializer):
    category = serializers.StringRelatedField()
    avg_rating = serializers.FloatField(read_only=True, allow_null=True)

    class Meta:
        model = Product
        fields = (
            "id", "name", "slug", "description", "price", "category", "stock", "avg_rating",
        )


class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Review
        fields = ("id", "user", "rating", "comment", "created_at")
        read_only_fields = ("user", "created_at")


class OrderItemSerializer(serializers.ModelSerializer):
    product = serializers.StringRelatedField()

    class Meta:
        model = OrderItem
        fields = ("id", "product", "quantity", "price")


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = (
            "id", "status", "total_price", "full_name", "email", "phone",
            "shipping_address", "items", "created_at",
        )
        read_only_fields = ("status", "total_price", "items", "created_at")


class CartItemSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.active())
    product_name = serializers.StringRelatedField(source="product", read_only=True)
    quantity = serializers.IntegerField(min_value=1, max_value=10_000)

    class Meta:
        model = CartItem
        fields = ("id", "product", "product_name", "quantity")


class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ("id", "username", "email", "password")

    def validate_email(self, value: str) -> str:
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Користувач з такою поштою вже існує.")
        return value

    def create(self, validated_data: dict[str, Any]) -> User:
        return User.objects.create_user(**validated_data)
