"""Налаштування для продакшену.

Усі секрети приходять лише з оточення: SECRET_KEY обов'язковий (без дефолта),
щоб прод не стартував із небезпечним ключем непомітно.
"""
from .base import *

DEBUG = False

SECRET_KEY = env("SECRET_KEY")  # обов'язково з оточення

# Стиснута статика з хешами імен — обслуговується WhiteNoise.
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

# Довіряти X-Forwarded-Proto лише коли реально стоїть TLS-проксі (вмикається через env).
if env.bool("USE_PROXY_SSL_HEADER", default=False):
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# HTTPS-хардненг. Дефолти вимкнені, бо локальний docker compose працює по HTTP;
# у реальному деплої за TLS-проксі вмикаються через env.
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=False)
SESSION_COOKIE_SECURE = env.bool("SESSION_COOKIE_SECURE", default=False)
CSRF_COOKIE_SECURE = env.bool("CSRF_COOKIE_SECURE", default=False)
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=0)
