from django.urls import path

from . import views

app_name = "products"

urlpatterns = [
    path("", views.ProductListView.as_view(), name="list"),
    # Spec also requires /products/; same catalog. Separate name since URL names must be unique.
    path("products/", views.ProductListView.as_view(), name="list_alt"),
    path("product/<slug:slug>/", views.ProductDetailView.as_view(), name="detail"),
]
