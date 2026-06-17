# Async Email Delivery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Send order emails asynchronously via Celery with automatic retry on transient failures, plus a manual admin resend — so a core feature stops blocking checkout and stops losing emails silently.

**Architecture:** `create_order`'s `on_commit` enqueues one Celery task per email (`customer`/`admin`). A Redis-backed worker sends each; transient SMTP errors auto-retry with backoff. Tests run Celery eagerly (inline) so no broker/worker is needed.

**Tech Stack:** Celery 5 + Redis, Django 5.2, pytest-django.

Spec: `docs/superpowers/specs/2026-06-17-async-email-design.md`.

---

### Task 1: Celery scaffolding

**Files:**
- Modify: `pyproject.toml` (dep `celery[redis]`; mypy override; pytest settings module)
- Create: `config/celery.py`
- Modify: `config/__init__.py`
- Modify: `config/settings/base.py` (Celery settings)
- Create: `config/settings/test.py`

- [ ] **Step 1: Add dependency**

```bash
uv add 'celery[redis]'
```

- [ ] **Step 2: Create the Celery app** — `config/celery.py`

```python
import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

app = Celery("config")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
```

- [ ] **Step 3: Load the app on startup** — `config/__init__.py`

```python
from .celery import app as celery_app

__all__ = ("celery_app",)
```

- [ ] **Step 4: Celery settings** — append after the `SITE_URL` line in `config/settings/base.py`

```python
# Celery — async tasks (order emails) with auto-retry; tests set ALWAYS_EAGER
CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="redis://localhost:6379/0")
CELERY_TASK_ALWAYS_EAGER = env.bool("CELERY_TASK_ALWAYS_EAGER", default=False)
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
```

- [ ] **Step 5: Test settings** — create `config/settings/test.py`

```python
from .dev import *

# Run Celery tasks inline (no broker/worker needed in tests).
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
```

- [ ] **Step 6: Point pytest at test settings + ignore celery in mypy** — `pyproject.toml`

Change `DJANGO_SETTINGS_MODULE = "config.settings.dev"` → `"config.settings.test"` under `[tool.pytest.ini_options]`.
Add `"celery.*"` to the `ignore_missing_imports` module list.

- [ ] **Step 7: Verify nothing broke**

Run: `docker compose up -d --wait db && uv run ruff check . && uv run mypy . && uv run pytest`
Expected: ruff/mypy clean, 99 passed (services still sends inline — unchanged behavior).

- [ ] **Step 8: Commit**

```bash
git add -A && git commit -m "feat(email): add Celery + Redis scaffolding"
```

---

### Task 2: `send_order_email` task

**Files:**
- Create: `orders/tasks.py`
- Test: `orders/tests/test_tasks.py`

- [ ] **Step 1: Write the failing test** — `orders/tests/test_tasks.py`

```python
"""Order email Celery task tests (run eagerly)."""
from decimal import Decimal
from typing import cast

import pytest
from django.core import mail
from django.test import override_settings

from orders.models import Order, OrderItem
from orders.tasks import send_order_email
from products.models import Product
from products.tests.factories import ProductFactory
from users.models import User
from users.tests.factories import UserFactory


def _order(user: User) -> Order:
    order = Order.objects.create(
        user=user, status=Order.Status.PAID, full_name="Buyer", email="b@e.com",
        phone="1", shipping_address="addr", total_price=Decimal("20.00"),
    )
    product = cast(Product, ProductFactory(price=Decimal("10.00"), stock=48))
    OrderItem.objects.create(order=order, product=product, quantity=2, price=Decimal("10.00"))
    return order


@pytest.mark.django_db
@override_settings(DEFAULT_FROM_EMAIL="shop@shop.test")
def test_send_order_email_customer() -> None:
    order = _order(cast(User, UserFactory()))
    send_order_email(order.pk, "customer")
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ["b@e.com"]
    assert f"#{order.pk}" in mail.outbox[0].subject


@pytest.mark.django_db
@override_settings(ADMINS=[("Admin", "admin@shop.test")])
def test_send_order_email_admin() -> None:
    order = _order(cast(User, UserFactory()))
    send_order_email(order.pk, "admin")
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ["admin@shop.test"]
```

- [ ] **Step 2: Run it — verify it fails**

Run: `uv run pytest orders/tests/test_tasks.py -v`
Expected: FAIL (ImportError: cannot import name `send_order_email`).

- [ ] **Step 3: Implement the task** — `orders/tasks.py`

```python
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
```

- [ ] **Step 4: Run it — verify it passes**

Run: `uv run pytest orders/tests/test_tasks.py -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "feat(email): send_order_email Celery task with auto-retry"
```

---

### Task 3: Enqueue from `create_order` (replace inline send)

**Files:**
- Modify: `orders/services.py`
- Test: `orders/tests/test_services.py` (existing email tests — must stay green)

- [ ] **Step 1: Replace imports + the email functions** — `orders/services.py`

Change the import block top to (drop `Any`, `EmailMultiAlternatives`, `render_to_string`; add tasks import):

```python
from dataclasses import dataclass
from decimal import Decimal

from django.conf import settings
from django.db import transaction

from products.models import Product
from users.models import User

from .models import Order, OrderItem
from .tasks import send_order_email
```

Replace `_send_order_emails` and delete `_send_email`:

```python
def _send_order_emails(order: Order) -> None:
    send_order_email.delay(order.pk, "customer")
    if any(email for _, email in settings.ADMINS):
        send_order_email.delay(order.pk, "admin")
```

- [ ] **Step 2: Run the existing email tests — they stay green (eager)**

Run: `uv run pytest orders/tests/test_services.py -v`
Expected: PASS — `test_create_order_emails_customer_and_admin` (2 emails, recipients, subjects, bodies, HTML, `50→48` admin stock) and `test_order_email_skipped_without_admins` (1 email) pass via eager tasks.

- [ ] **Step 3: Commit**

```bash
git add -A && git commit -m "feat(email): enqueue order emails via Celery on commit"
```

---

### Task 4: Retry on transient failure

**Files:**
- Test: `orders/tests/test_tasks.py`

- [ ] **Step 1: Write the failing test** — append to `orders/tests/test_tasks.py`

```python
import smtplib
from unittest import mock


@pytest.mark.django_db
@override_settings(DEFAULT_FROM_EMAIL="shop@shop.test")
def test_send_order_email_retries_on_transient_error() -> None:
    order = _order(cast(User, UserFactory()))
    real_send = EmailMultiAlternatives.send
    calls = {"n": 0}

    def flaky(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        calls["n"] += 1
        if calls["n"] == 1:
            raise smtplib.SMTPException("temporary")
        return real_send(self, *args, **kwargs)

    with mock.patch.object(EmailMultiAlternatives, "send", flaky):
        send_order_email(order.pk, "customer")

    assert calls["n"] == 2          # failed once, retried, then succeeded
    assert len(mail.outbox) == 1    # delivered after retry
```

Add the import at the top of the file: `from django.core.mail import EmailMultiAlternatives`.

- [ ] **Step 2: Run it**

Run: `uv run pytest orders/tests/test_tasks.py::test_send_order_email_retries_on_transient_error -v`
Expected: PASS — the task's `autoretry_for` re-runs the task inline (eager), the 2nd `send` succeeds. (If eager retry does not re-execute, this exposes it now; adjust the task/test before moving on.)

- [ ] **Step 3: Commit**

```bash
git add -A && git commit -m "test(email): verify task retries on transient SMTP error"
```

---

### Task 5: Admin "resend" action

**Files:**
- Modify: `orders/admin.py`
- Test: `orders/tests/test_tasks.py`

- [ ] **Step 1: Write the failing test** — append to `orders/tests/test_tasks.py`

```python
from django.contrib.admin.sites import AdminSite
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory


@pytest.mark.django_db
@override_settings(ADMINS=[("Admin", "admin@shop.test")], DEFAULT_FROM_EMAIL="shop@shop.test")
def test_admin_resend_action_sends_both() -> None:
    from orders.admin import OrderAdmin

    order = _order(cast(User, UserFactory()))
    req = RequestFactory().post("/admin/")
    setattr(req, "session", {})
    setattr(req, "_messages", FallbackStorage(req))
    OrderAdmin(Order, AdminSite()).resend_emails(req, Order.objects.filter(pk=order.pk))
    assert len(mail.outbox) == 2  # customer + admin (eager)
```

- [ ] **Step 2: Run it — verify it fails**

Run: `uv run pytest orders/tests/test_tasks.py::test_admin_resend_action_sends_both -v`
Expected: FAIL (`OrderAdmin` has no attribute `resend_emails`).

- [ ] **Step 3: Implement the action** — `orders/admin.py`

Add imports near the top: `from django.conf import settings` and `from .tasks import send_order_email`.
Add `"resend_emails"` to `OrderAdmin.actions` and the method:

```python
    @admin.action(description="Надіслати листи ще раз")
    def resend_emails(self, request: HttpRequest, queryset: QuerySet[Order]) -> None:
        has_admins = any(email for _, email in settings.ADMINS)
        for order in queryset:
            send_order_email.delay(order.pk, "customer")
            if has_admins:
                send_order_email.delay(order.pk, "admin")
        self.message_user(request, "Листи поставлено в чергу на повторну відправку.", messages.SUCCESS)
```

- [ ] **Step 4: Run it — verify it passes**

Run: `uv run pytest orders/tests/test_tasks.py -v`
Expected: PASS (all task tests).

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "feat(email): admin action to resend order emails"
```

---

### Task 6: docker-compose — redis + celery worker

**Files:**
- Modify: `docker-compose.yml`
- Modify: `.env.example`

- [ ] **Step 1: Add redis + worker services and broker env**

Add a `redis` service (`image: redis:7`, `ports: ["6379:6379"]`, healthcheck `redis-cli ping`).
Add a `celery` service: `build: .`, `entrypoint: ["celery", "-A", "config", "worker", "-l", "info"]` (bypasses the web entrypoint's migrate/collectstatic), same `environment` as `web` plus `CELERY_BROKER_URL: redis://redis:6379/0`, `depends_on: [db (healthy), redis (healthy)]`.
Add `CELERY_BROKER_URL: redis://redis:6379/0` to the `web` service env; add `redis` to web `depends_on`.

- [ ] **Step 2: Document broker in `.env.example`**

Append:
```
# Celery broker (async order emails)
CELERY_BROKER_URL=redis://localhost:6379/0
```

- [ ] **Step 3: Verify compose config is valid**

Run: `docker compose config >/dev/null && echo OK`
Expected: `OK` (no YAML/compose errors).

- [ ] **Step 4: Commit**

```bash
git add -A && git commit -m "feat(email): redis + celery worker in docker-compose"
```

---

### Task 7: README — async email section

**Files:**
- Modify: `README.md`, `README.uk.md`

- [ ] **Step 1: Add a subsection under "Email notifications"** (both languages)

EN — after the existing email backend paragraph:

```markdown
### Reliable delivery (Celery)

Order emails are sent **asynchronously** via a Celery task (Redis broker): checkout
never blocks on SMTP, and transient failures (e.g. a provider rate-limit) **auto-retry**
with backoff instead of being silently dropped. Staff can re-send an order's emails from
the admin (Orders → action "Надіслати листи ще раз").

Run locally: `docker compose up -d db redis`, then `uv run celery -A config worker -l info`
alongside `runserver` (or `docker compose up` for the full stack). Tests run tasks inline
(`CELERY_TASK_ALWAYS_EAGER`), so no broker is needed in CI.

A dedicated email-event table or a Flower dashboard would be overkill for this feature —
Celery's retry plus the admin resend cover reliable delivery.
```

UK — equivalent translation under «Email-сповіщення».

- [ ] **Step 2: Commit**

```bash
git add -A && git commit -m "docs: README async email (Celery) section"
```

---

### Task 8: Final verification

- [ ] **Step 1: Full gate**

Run: `uv run ruff check . && uv run mypy . && uv run pytest`
Expected: ruff/mypy clean; all tests pass (≈102), coverage ≥80%.

- [ ] **Step 2: Smoke-test the real path** (redis + worker + a live order) — optional manual check, then hand off to `superpowers:finishing-a-development-branch`.

---

## Self-Review

**Spec coverage:** celery app + settings (Task 1) ✓; task with autoretry (Task 2) ✓; enqueue on commit (Task 3) ✓; retry behavior (Task 4) ✓; admin resend (Task 5) ✓; docker-compose redis+worker (Task 6) ✓; README incl. "overkill" note (Task 7) ✓; eager test mode (Task 1/test.py) ✓. No spec requirement left unimplemented.

**Placeholder scan:** none — every code step has full code.

**Type consistency:** `send_order_email(order_id: int, kind: str)` used identically in tasks, services, admin, and tests; `_KINDS` keys `"customer"`/`"admin"` consistent throughout.
