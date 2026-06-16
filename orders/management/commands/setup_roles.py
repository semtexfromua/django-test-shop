"""Create the Managers role group with order permissions."""
from typing import Any

from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create the Managers group with view/change permissions on orders (idempotent)."

    def handle(self, *args: Any, **options: Any) -> None:
        group, _ = Group.objects.get_or_create(name="Managers")
        perms = Permission.objects.filter(
            content_type__app_label="orders",
            codename__in=["view_order", "change_order"],
        )
        group.permissions.set(perms)
        self.stdout.write(self.style.SUCCESS("Managers group configured."))
