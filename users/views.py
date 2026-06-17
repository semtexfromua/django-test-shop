from typing import Any, cast

from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import QuerySet
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView

from .forms import ProfileForm, RegisterForm
from .models import User


class RegisterView(CreateView):
    """Registration with automatic login after the account is created."""

    form_class = RegisterForm
    template_name = "users/register.html"
    success_url = reverse_lazy("users:profile")

    def form_valid(self, form: RegisterForm) -> HttpResponse:
        response = super().form_valid(form)
        login(self.request, form.instance)
        return response


class ProfileView(LoginRequiredMixin, UpdateView):
    form_class = ProfileForm
    template_name = "users/profile.html"
    success_url = reverse_lazy("users:profile")

    def get_object(self, queryset: QuerySet[Any] | None = None) -> User:
        return cast(User, self.request.user)
