from django.conf import settings
from django.contrib import admin
from django.urls import URLPattern, URLResolver, include, path, re_path
from django.views.decorators.csrf import csrf_exempt
from django.views.static import serve
from graphene_django.views import GraphQLView
from graphql.validation import ASTValidationRule, NoSchemaIntrospectionCustomRule


def graphql_validation_rules() -> list[type[ASTValidationRule]]:
    """Disable introspection in prod (schema disclosure); keep it in dev for GraphiQL."""
    return [] if settings.DEBUG else [NoSchemaIntrospectionCustomRule]


urlpatterns: list[URLResolver | URLPattern] = [
    path("admin/", admin.site.urls),
    path("api/", include("api.urls")),
    path(
        "graphql/",
        csrf_exempt(
            GraphQLView.as_view(
                graphiql=settings.DEBUG, validation_rules=graphql_validation_rules()
            )
        ),
        name="graphql",
    ),
    path("account/", include("users.urls")),
    path("", include("orders.urls")),
    path("", include("reviews.urls")),
    path("", include("products.urls")),
]

# Media under gunicorn (demo deploy). For real production — nginx/CDN/object storage.
urlpatterns += [
    re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
]
