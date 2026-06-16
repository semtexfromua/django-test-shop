"""Адмінка каталогу."""
from django.contrib import admin
from django.db.models import QuerySet, Sum
from django.http import HttpRequest

from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "parent")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "stock", "is_active", "sold")
    list_filter = ("category", "is_active")
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}
    list_editable = ("price", "stock", "is_active")

    def get_queryset(self, request: HttpRequest) -> QuerySet[Product]:
        return super().get_queryset(request).annotate(_sold=Sum("order_items__quantity"))

    @admin.display(description="Продано", ordering="_sold")
    def sold(self, obj: Product) -> int:
        return getattr(obj, "_sold", 0) or 0
