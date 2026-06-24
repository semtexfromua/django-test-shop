from decimal import Decimal
from typing import Any

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand

from products.models import Category, Product

# (name, parent|None) — parents before children; demonstrates nested categories
CATEGORY_TREE: list[tuple[str, str | None]] = [
    ("Ingredients", None),
    ("Kits", None),
    ("Hops", "Ingredients"),
    ("Malts", "Ingredients"),
    ("Yeast", "Ingredients"),
]

# (name, category, price, stock, image) — image lives in static/img/products/
PRODUCTS: list[tuple[str, str, str, int, str]] = [
    ("Cascade Hops", "Hops", "4.50", 100, "cascade_hops.jpg"),
    ("Centennial Hops", "Hops", "5.00", 80, "centennial_hops.jpg"),
    ("Citra Hops", "Hops", "6.50", 60, "citra_hops.jpg"),
    ("Mosaic Hops", "Hops", "6.75", 50, "mosaic_hops.jpg"),
    ("Saaz Hops", "Hops", "5.25", 70, "saaz_hops.jpg"),
    ("Maris Otter Malt", "Malts", "2.20", 200, "maris_otter_malt.jpg"),
    ("Pilsner Malt", "Malts", "2.00", 200, "pilsner_malt.jpg"),
    ("Caramel Malt", "Malts", "2.50", 150, "caramel_malt.jpg"),
    ("Unmalted Wheat", "Malts", "1.90", 180, "unmalted_wheat.jpg"),
    ("Safale US-05 Yeast", "Yeast", "3.80", 120, "safale_us05_yeast.jpg"),
    ("Imperial Yeast", "Yeast", "8.00", 40, "imperial_yeast.jpg"),
    ("West Coast IPA Kit", "Kits", "39.99", 25, "ipa_kit.jpg"),
]


class Command(BaseCommand):
    help = "Create demo categories and products with images (idempotent)."

    def handle(self, *args: Any, **options: Any) -> None:
        cats: dict[str, Category] = {}
        for name, parent_name in CATEGORY_TREE:
            parent = cats[parent_name] if parent_name else None
            cats[name], _ = Category.objects.get_or_create(name=name, defaults={"parent": parent})
        img_dir = settings.BASE_DIR / "static" / "img" / "products"
        for name, cat_name, price, stock, image in PRODUCTS:
            product, _ = Product.objects.get_or_create(
                name=name,
                defaults={
                    "category": cats[cat_name],
                    "price": Decimal(price),
                    "stock": stock,
                    "description": f"{name} — демо-товар.",
                },
            )
            # Re-attach the image if its media file is missing.
            # Render's free tier has an ephemeral disk — media is wiped on every
            # redeploy/wake, so we restore it from the persistent static/ source.
            src = img_dir / image
            media_missing = not product.image or not product.image.storage.exists(product.image.name)
            if src.exists() and media_missing:
                with src.open("rb") as fh:
                    product.image.save(image, File(fh), save=True)
        self.stdout.write(self.style.SUCCESS("Catalog populated."))
