from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from . import views

app_name = "api"

router = DefaultRouter()
router.register("products", views.ProductViewSet, basename="product")
router.register("orders", views.OrderViewSet, basename="order")
router.register("cart", views.CartItemViewSet, basename="cart")

urlpatterns = [
    path("", include(router.urls)),
    path("products/<int:pk>/reviews/", views.ProductReviewsView.as_view(), name="product-reviews"),
    path("users/register/", views.RegisterAPIView.as_view(), name="register"),
    path("users/login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("users/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="api:schema"), name="docs"),
]
