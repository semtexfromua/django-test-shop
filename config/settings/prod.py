"""Налаштування для продакшену.

SECRET_KEY та ALLOWED_HOSTS обов'язково мають приходити з оточення (див. base).
"""
from .base import *  # noqa: F403

DEBUG = False

# Стиснута статика з хешами імен — обслуговується WhiteNoise.
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
