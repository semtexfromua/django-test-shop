import smtplib

from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from .models import Order

# kind -> (subject prefix, template base under templates/emails/)
_KINDS = {
    "customer": ("Замовлення", "emails/order_confirmation"),
    "admin": ("Нове замовлення", "emails/order_admin"),
}


@shared_task(
    autoretry_for=(smtplib.SMTPException, OSError),
    retry_backoff=True,
    retry_backoff_max=600,
    max_retries=5,
)
def send_order_email(order_id: int, kind: str) -> None:
    """Send one order email (``customer`` or ``admin``); retried on transient SMTP errors."""
    order = Order.objects.get(pk=order_id)
    label, template = _KINDS[kind]
    recipients = [order.email] if kind == "customer" else [e for _, e in settings.ADMINS]
    ctx = {
        "order": order,
        "items": list(order.items.select_related("product")),
        "site_url": settings.SITE_URL,
    }
    message = EmailMultiAlternatives(
        f"{label} #{order.pk}",
        render_to_string(f"{template}.txt", ctx),
        settings.DEFAULT_FROM_EMAIL,
        recipients,
    )
    message.attach_alternative(render_to_string(f"{template}.html", ctx), "text/html")
    message.send()  # no fail_silently — failures raise so Celery retries
