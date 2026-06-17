from django.urls import path

from . import views

app_name = "reviews"

urlpatterns = [
    path("product/<slug:slug>/review/", views.ReviewCreateView.as_view(), name="create"),
]
