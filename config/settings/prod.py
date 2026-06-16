"""Production settings.

All secrets come from the environment only: SECRET_KEY is required (no default)
so production never silently starts with an insecure key.
"""
from .base import *

DEBUG = False

SECRET_KEY = env("SECRET_KEY")  # required from the environment

# Compressed, hashed-name static files served by WhiteNoise.
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

# Trust X-Forwarded-Proto only when a TLS proxy is actually in front (enabled via env).
if env.bool("USE_PROXY_SSL_HEADER", default=False):
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# HTTPS hardening. Off by default because local docker compose runs over HTTP;
# in a real deployment behind a TLS proxy these are enabled via env.
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=False)
SESSION_COOKIE_SECURE = env.bool("SESSION_COOKIE_SECURE", default=False)
CSRF_COOKIE_SECURE = env.bool("CSRF_COOKIE_SECURE", default=False)
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=0)
