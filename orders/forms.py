from typing import Any

from django import forms

from .models import Order

METHOD_CHOICES = [("card", "Картка"), ("cash", "Готівка при отриманні")]


class OrderForm(forms.ModelForm):
    method = forms.ChoiceField(choices=METHOD_CHOICES, label="Спосіб оплати")

    class Meta:
        model = Order
        fields = ("full_name", "email", "phone", "shipping_address")

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "Input")
