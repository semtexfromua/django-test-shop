# Async Email Delivery — Design

**Date:** 2026-06-17 · **Status:** approved

## Context & problem

Order emails (customer confirmation + admin notification) are sent **synchronously**
inside `create_order`'s `transaction.on_commit`, via `EmailMultiAlternatives` with
`fail_silently=True`. Email is a core feature, but the current implementation:

- **blocks** the checkout request/worker while SMTP runs;
- **silently loses** failures (`fail_silently=True`) — observed: a provider rate-limit
  dropped the admin email with no trace;
- has **no retry** on transient failures and **no way to resend**.

## Goal

Reliable **asynchronous** email delivery: enqueue on commit, send in a background
worker with **automatic retry/backoff** on transient errors (no silent loss), plus a
**manual resend** path for staff.

## Approach (decided)

**Celery + Redis** — the standard async task queue for Django. Transient SMTP failures
(including free-tier provider rate limits) auto-retry until they succeed. Lean scope:
no event-log model, no result backend.

## Components

- **`config/celery.py`** — Celery app: `config_from_object("django.conf:settings",
  namespace="CELERY")`, `autodiscover_tasks()`. **`config/__init__.py`** imports it so
  `@shared_task` registers on Django startup.
- **Settings (`config/settings/base.py`):**
  - `CELERY_BROKER_URL` (env, default `redis://localhost:6379/0`)
  - `CELERY_TASK_ALWAYS_EAGER` (env, default `False`)
  - `CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True`
- **`config/settings/test.py`** — inherits dev, sets `CELERY_TASK_ALWAYS_EAGER = True`
  and `CELERY_TASK_EAGER_PROPAGATES = True`; `pytest` points at it so tasks run inline
  (no broker/worker needed in tests or CI).
- **`orders/tasks.py`** — `send_order_email(order_id, kind)` Celery task. **One email per
  task** so retrying the admin email never re-sends the customer one. Decorated with
  `autoretry_for=(smtplib.SMTPException, OSError)`, `retry_backoff=True`,
  `retry_backoff_max=600`, `max_retries=5`. Renders the existing `emails/order_*`
  templates and calls `message.send()` **without** `fail_silently` (failures raise → retry).
- **`orders/services.py`** — `_send_order_emails(order)` (still invoked from `create_order`
  on commit) now only **enqueues**: `send_order_email.delay(pk, "customer")` and, when
  `ADMINS` is set, `send_order_email.delay(pk, "admin")`. The inline send helper is removed.
- **`orders/admin.py`** — `OrderAdmin` action "Надіслати листи ще раз" re-enqueues both
  emails for the selected orders (manual resend).
- **`docker-compose.yml`** — `redis` service (published on 6379 for local dev) + `celery`
  worker service (`celery -A config worker -l info`); `CELERY_BROKER_URL` on web + worker.
- **Dependency:** `celery[redis]`.

## Data flow

checkout (web) / API → `create_order` (atomic: stock check, price snapshot, decrement) →
on commit → enqueue 2 tasks → worker sends each email → transient failure (e.g. SMTP
rate-limit) → Celery auto-retries with exponential backoff → delivered. Manual resend =
admin action re-enqueues the same tasks.

## Error handling

- **Transient** (`smtplib.SMTPException`, `OSError`, provider rate-limit): auto-retry,
  exponential backoff, capped at 10 min, up to 5 attempts.
- **Permanent** (`Order.DoesNotExist`): not retried → task fails and is logged by Celery.
- **Exhausted retries:** logged by Celery; staff resend via the admin action.

## Testing (TDD)

Tests run with `CELERY_TASK_ALWAYS_EAGER=True` (test settings) → tasks execute inline,
Django's locmem backend populates `mail.outbox`.

1. Order placement sends customer + admin emails (recipients, subjects, text + HTML
   bodies, admin-only stock change) — adapted to the eager-task path.
2. Admin email is skipped when `ADMINS` is empty.
3. **Retry:** mock `EmailMultiAlternatives.send` to raise `SMTPException` once, then
   succeed; assert the task retries and the email is ultimately delivered.
4. **Resend:** the admin action enqueues (and, eager, sends) both emails for an order.

## Non-goals (deliberate — would be overkill for this feature)

- **Event-log model** (per-email status rows): Celery's retry + the admin resend cover
  the real need; a dedicated table adds a model/migration/status-tracking for little gain.
- **Flower / monitoring UI, result backend, Celery beat, multiple queues, open/click
  tracking** — out of scope for a single transactional-email feature.

## Documentation

README gets an **additional section** explaining that async delivery via Celery is what
makes order emails *reliable* (non-blocking checkout + auto-retry, no silent loss), and
noting that a dedicated event-log model and Flower would be overkill for this feature.

## Ops / local dev

- **Local:** `docker compose up -d db redis`, then run `celery -A config worker -l info`
  and `manage.py runserver`. Emails go to the configured backend (Mailtrap via `.env`);
  retries absorb the free-tier rate limit.
- **Tests / CI:** eager mode — no broker or worker required.
