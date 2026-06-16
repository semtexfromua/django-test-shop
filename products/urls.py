"""URL-и каталогу."""
from django.urls import path

from . import views

app_name = "products"

urlpatterns = [
    path("", views.ProductListView.as_view(), name="list"),
    path("products/", views.ProductListView.as_view(), name="list_alt"),
    path("product/<slug:slug>/", views.ProductDetailView.as_view(), name="detail"),
]
