"""Smoke-тести фундаменту проєкту."""
import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse


def test_custom_user_model_configured() -> None:
    """Проєкт використовує кастомну модель користувача."""
    assert settings.AUTH_USER_MODEL == "users.User"


@pytest.mark.django_db
def test_custom_user_can_be_created() -> None:
    """Кастомного користувача можна створити — міграція й AUTH_USER_MODEL робочі."""
    user = get_user_model().objects.create_user(username="alice", password="pw-test-12345")
    assert user.pk is not None
    assert user.username == "alice"


@pytest.mark.django_db
def test_admin_login_page_loads(client: Client) -> None:
    """Сторінка входу в адмінку віддається — URL-конфіг і шаблони працюють."""
    response = client.get(reverse("admin:login"))
    assert response.status_code == 200
