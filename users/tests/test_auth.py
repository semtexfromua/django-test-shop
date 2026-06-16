"""Тести автентифікації та кабінету."""
import pytest
from django.test import Client
from django.urls import reverse

from users.models import User


@pytest.mark.django_db
def test_register_creates_and_logs_in(client: Client) -> None:
    resp = client.post(
        reverse("users:register"),
        {
            "username": "alice",
            "email": "a@e.com",
            "password1": "Str0ngPwd!23",
            "password2": "Str0ngPwd!23",
        },
    )
    assert resp.status_code == 302
    assert User.objects.filter(username="alice").exists()
    assert "_auth_user_id" in client.session


@pytest.mark.django_db
def test_login_logout(client: Client) -> None:
    User.objects.create_user(username="bob", password="Str0ngPwd!23")
    ok = client.post(reverse("users:login"), {"username": "bob", "password": "Str0ngPwd!23"})
    assert ok.status_code == 302
    assert "_auth_user_id" in client.session
    client.post(reverse("users:logout"))
    assert "_auth_user_id" not in client.session


@pytest.mark.django_db
def test_profile_requires_login(client: Client) -> None:
    resp = client.get(reverse("users:profile"))
    assert resp.status_code == 302
    assert reverse("users:login") in resp["Location"]


@pytest.mark.django_db
def test_profile_edit_updates(client: Client) -> None:
    User.objects.create_user(username="carol", password="Str0ngPwd!23")
    client.login(username="carol", password="Str0ngPwd!23")
    resp = client.post(
        reverse("users:profile"),
        {"first_name": "Carol", "last_name": "Smith", "email": "c@e.com"},
    )
    assert resp.status_code == 302
    u = User.objects.get(username="carol")
    assert u.first_name == "Carol"
    assert u.email == "c@e.com"


@pytest.mark.django_db
def test_password_change(client: Client) -> None:
    User.objects.create_user(username="dave", password="OldPwd!2345")
    client.login(username="dave", password="OldPwd!2345")
    resp = client.post(
        reverse("users:password_change"),
        {
            "old_password": "OldPwd!2345",
            "new_password1": "NewPwd!67890",
            "new_password2": "NewPwd!67890",
        },
    )
    assert resp.status_code == 302
    u = User.objects.get(username="dave")
    assert u.check_password("NewPwd!67890")
