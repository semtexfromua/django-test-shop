# Аудит проєкту — автономний хардненг

Багатоцикловий аудит: 5 циклів `рев'ю → фікс → verify → commit`, далі spec-gap перевірка,
далі повний Playwright-прохід. Працюю автономно, поки є відкриті пункти.

**Статус: IN PROGRESS**

Базовий стан перед аудитом: 80 тестів, coverage 94.93%, ruff/mypy чисті, 8 юнітів на `main`.

Легенда severity: 🔴 Critical · 🟠 Important · 🟡 Minor. Статус: ⬜ open · ✅ fixed · ⏭️ wontfix(з причиною).

---

## Цикл 1 — Коректність і бізнес-логіка
Рев'ю: 2 субагенти (orders/payments/reviews-ядро + catalog/users/analytics), баги відтворювали емпірично.

### Знахідки
- ✅ 🔴 **C1** `orders/services.py` — checkout продавав деактивовані товари (`cart.__iter__` брав `Product.objects`, не `.active()`; `create_order` не перевіряв `is_active`). Фікс: lock `filter(pk__in, is_active=True)` → `InsufficientStock`. Покрито web+API. +тест.
- ✅ 🟠 **C2** дабл-сабміт checkout → дублі замовлень/оплат/списань. Фікс: guard від повторного сабміту у формі (`dataset.sent`). Залишок: одночасні запити (concurrent) — потребує idempotency-key, відкладено й задокументовано тут.
- ✅ 🟠 **I1** `Cart.__len__` розходився з `__iter__`/`total()` при видаленні товару. Фікс: `__len__` через `__iter__`. +тест.
- ✅ 🟠 **slug-колізія** (різні назви → однаковий slug) і не-Latin назви (порожній slug) → IntegrityError 500. Фікс: `_unique_slug` (суфікс `-2/-3…` + fallback) у `Category`/`Product.save`. +2 тести.
- ✅ 🟡 API register не вимагав email (вебформа вимагає). Фікс: `email` обов'язковий у `RegisterSerializer`. +тест.
- ⏭️ 🟡 `Category` self-parent/цикли — латентне (нема tree-walking коду); YAGNI, відкладено.
- Перевірено чистим (не баги): snapshot ціни, оверселл(sequential), atomic+email rollback, cancel-ідемпотентність, reviews-authz, catalog query-params/пагінація/avg_rating, analytics.

### Результат
ruff/mypy чисті, pytest **85 passed**, coverage 95.12%. Побічно: прибрано зайвий `type: ignore` у `products/views.py`.

---

## Цикл 2 — Безпека та авторизація
_(authz, JWT, CSRF, ін'єкції, витік даних, permissions)_

---

## Цикл 3 — Веб UI / в'юхи / шаблони
_(форми, обробка помилок, XSS, биті лінки, UX)_

---

## Цикл 4 — API та цілісність даних
_(DRF, серіалізатори, валідація, N+1, граничні)_

---

## Цикл 5 — Крос-катінг / консистентність / конфіг / тести
_(settings, Docker, якість тестів, мертвий код, узгодженість)_

---

## Spec-gap перевірка (проти `docs/06 Project M3-1.md`)
_(заповнюється)_

---

## Повний Playwright-прохід
_(заповнюється)_
