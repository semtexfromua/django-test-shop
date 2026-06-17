from typing import cast

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import IntegrityError
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from products.models import Product
from users.models import User

from .forms import ReviewForm
from .services import can_review


class ReviewCreateView(LoginRequiredMixin, View):
    """Create a review — only after purchasing the product (once per product)."""

    def _product(self) -> Product:
        return get_object_or_404(Product.objects.active(), slug=self.kwargs["slug"])

    def get(self, request: HttpRequest, slug: str) -> HttpResponse:
        product = self._product()
        if not can_review(cast(User, request.user), product):
            messages.info(request, "Відгук можна залишити лише після покупки (один раз).")
            return redirect(product.get_absolute_url())
        return render(
            request, "reviews/review_form.html", {"product": product, "form": ReviewForm()}
        )

    def post(self, request: HttpRequest, slug: str) -> HttpResponse:
        product = self._product()
        if not can_review(cast(User, request.user), product):
            messages.error(request, "Ви не можете залишити відгук на цей товар.")
            return redirect(product.get_absolute_url())
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.user = cast(User, request.user)
            try:
                review.save()
            except IntegrityError:  # race: duplicate on unique(product, user)
                messages.error(request, "Ви вже залишили відгук на цей товар.")
                return redirect(product.get_absolute_url())
            messages.success(request, "Дякуємо за відгук!")
            return redirect(product.get_absolute_url())
        return render(
            request, "reviews/review_form.html", {"product": product, "form": form}
        )
