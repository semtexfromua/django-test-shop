"""URL-и каталогу."""
from django.urls import path

from . import views

app_name = "products"

urlpatterns = [
    path("", views.ProductListView.as_view(), name="list"),
    # ТЗ вимагає і /products/; той самий каталог. Окрема назва, бо ім'я має бути унікальним.
    path("products/", views.ProductListView.as_view(), name="list_alt"),
    path("product/<slug:slug>/", views.ProductDetailView.as_view(), name="detail"),
]
