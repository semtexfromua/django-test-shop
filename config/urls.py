"""Кореневий URL-конфіг проєкту."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import URLPattern, URLResolver, include, path
from django.views.decorators.csrf import csrf_exempt
from graphene_django.views import GraphQLView

urlpatterns: list[URLResolver | URLPattern] = [
    path("admin/", admin.site.urls),
    path("api/", include("api.urls")),
    path("graphql/", csrf_exempt(GraphQLView.as_view(graphiql=True)), name="graphql"),
    path("account/", include("users.urls")),
    path("", include("orders.urls")),
    path("", include("reviews.urls")),
    path("", include("products.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
