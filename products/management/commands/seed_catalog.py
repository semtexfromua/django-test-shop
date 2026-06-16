"""Наповнення каталогу демо-даними зі статичного шаблону Hop & Barley."""
from decimal import Decimal
from typing import Any

from django.core.management.base import BaseCommand

from products.models import Category, Product

CATEGORIES = ["Hops", "Malts", "Yeast", "Kits"]

# (name, category, price, stock)
PRODUCTS: list[tuple[str, str, str, int]] = [
    ("Cascade Hops", "Hops", "4.50", 100),
    ("Centennial Hops", "Hops", "5.00", 80),
    ("Citra Hops", "Hops", "6.50", 60),
    ("Mosaic Hops", "Hops", "6.75", 50),
    ("Saaz Hops", "Hops", "5.25", 70),
    ("Maris Otter Malt", "Malts", "2.20", 200),
    ("Pilsner Malt", "Malts", "2.00", 200),
    ("Caramel Malt", "Malts", "2.50", 150),
    ("Unmalted Wheat", "Malts", "1.90", 180),
    ("Safale US-05 Yeast", "Yeast", "3.80", 120),
    ("Imperial Yeast", "Yeast", "8.00", 40),
    ("West Coast IPA Kit", "Kits", "39.99", 25),
]


class Command(BaseCommand):
    help = "Створює демо-категорії та товари (ідемпотентно)."

    def handle(self, *args: Any, **options: Any) -> None:
        cats: dict[str, Category] = {}
        for name in CATEGORIES:
            cats[name], _ = Category.objects.get_or_create(name=name)
        for name, cat_name, price, stock in PRODUCTS:
            Product.objects.get_or_create(
                name=name,
                defaults={
                    "category": cats[cat_name],
                    "price": Decimal(price),
                    "stock": stock,
                    "description": f"{name} — демо-товар.",
                },
            )
        self.stdout.write(self.style.SUCCESS("Каталог наповнено."))
