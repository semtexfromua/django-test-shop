"""Форми користувачів."""
from typing import Any

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import User


def _style(form: forms.BaseForm) -> None:
    """Додає клас `.Input` до віджетів — для стилів шаблону Hop&Barley."""
    for field in form.fields.values():
        field.widget.attrs.setdefault("class", "Input")


class LoginForm(AuthenticationForm):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        _style(self)


class RegisterForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        _style(self)


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        _style(self)
