"""Створює групу ролей Managers з правами на замовлення."""
from typing import Any

from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Створює групу Managers з правами view/change на замовлення (ідемпотентно)."

    def handle(self, *args: Any, **options: Any) -> None:
        group, _ = Group.objects.get_or_create(name="Managers")
        perms = Permission.objects.filter(
            content_type__app_label="orders",
            codename__in=["view_order", "change_order"],
        )
        group.permissions.set(perms)
        self.stdout.write(self.style.SUCCESS("Групу Managers налаштовано."))
