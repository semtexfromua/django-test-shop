"""User forms."""
from typing import Any

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import User


def _style(form: forms.BaseForm) -> None:
    """Add the `.Input` class to widgets — for Hop & Barley template styling."""
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
        self.fields["email"].required = True  # email is required for notifications (orders)
        _style(self)

    def clean_email(self) -> str:
        email: str = self.cleaned_data["email"]
        if email and User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Користувач з такою поштою вже існує.")
        return email


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        _style(self)

    def clean_email(self) -> str:
        email: str = self.cleaned_data["email"]
        if email and User.objects.exclude(pk=self.instance.pk).filter(email__iexact=email).exists():
            raise forms.ValidationError("Користувач з такою поштою вже існує.")
        return email
