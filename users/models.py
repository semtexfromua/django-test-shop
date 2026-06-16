"""Users app models."""
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """Custom user model.

    For now it mirrors Django's default user exactly, but is split out from day one:
    changing `AUTH_USER_MODEL` later is painful and risky, so future fields
    (phone, addresses, etc.) will be added right here.
    """
