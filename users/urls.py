"""URL-и користувачів (префікс /account/)."""
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.urls import path, reverse_lazy

from . import views
from .forms import LoginForm

app_name = "users"

urlpatterns = [
    path("", views.ProfileView.as_view(), name="profile"),
    path("register/", views.RegisterView.as_view(), name="register"),
    path(
        "login/",
        LoginView.as_view(template_name="users/login.html", authentication_form=LoginForm),
        name="login",
    ),
    path("logout/", LogoutView.as_view(), name="logout"),
    path(
        "password/",
        PasswordChangeView.as_view(
            template_name="users/password_change.html",
            success_url=reverse_lazy("users:profile"),
        ),
        name="password_change",
    ),
]
