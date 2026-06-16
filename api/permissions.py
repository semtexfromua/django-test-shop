"""DRF-дозволи."""
from typing import Any

from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.views import APIView


class IsOwner(permissions.BasePermission):
    """Доступ до об'єкта лише власнику (`obj.user == request.user`)."""

    def has_object_permission(self, request: Request, view: APIView, obj: Any) -> bool:
        return bool(getattr(obj, "user", None) == request.user)
