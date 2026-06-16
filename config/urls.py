"""Кореневий URL-конфіг проєкту."""
from django.conf import settings
from django.contrib import admin
from django.urls import URLPattern, URLResolver, include, path, re_path
from django.views.decorators.csrf import csrf_exempt
from django.views.static import serve
from graphene_django.views import GraphQLView

urlpatterns: list[URLResolver | URLPattern] = [
    path("admin/", admin.site.urls),
    path("api/", include("api.urls")),
    path("graphql/", csrf_exempt(GraphQLView.as_view(graphiql=settings.DEBUG)), name="graphql"),
    path("account/", include("users.urls")),
    path("", include("orders.urls")),
    path("", include("reviews.urls")),
    path("", include("products.urls")),
]

# Медіа під gunicorn (demo-деплой). Для реального проду — nginx/CDN/обʼєктне сховище.
urlpatterns += [
    re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
]
