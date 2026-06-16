# Аудит проєкту — автономний хардненг

Багатоцикловий аудит: 5 циклів `рев'ю → фікс → verify → commit`, далі spec-gap перевірка,
далі повний Playwright-прохід. Працюю автономно, поки є відкриті пункти.

**Статус: РАУНД 2 IN PROGRESS** (раунд 1 завершено нижче). Раунд 1: 5 циклів + spec-gap + Playwright, 90 тестів, coverage 95.56%, ruff/mypy чисті.

Раунд 2 (нижче, секція «## Раунд 2»): ще 5 послідовних рев'ю-прогонів; фіксимо **Medium і вище**, Minor — лише нотатка.

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
Рев'ю: 2 субагенти (веб/сесії + API/JWT/GraphQL), bypass-спроби відтворювали емпірично.

### Знахідки
- **Реальних дір НЕ знайдено.** Веб: IDOR заблоковано (order/cart/profile/analytics scoped до `request.user`), authz скрізь (LoginRequired/UserPassesTest), CSRF на всіх POST, logout POST-only, без XSS/`|safe`, без mass-assignment, секрети git-ignored, prod вимагає SECRET_KEY з env. API: ownership/IsOwner/get_queryset scoped, read-only на status/total/price/user, register без is_staff, JWT 401, reviews-after-purchase server-side, GraphQL staff-gate на кожному резолвері, без raw SQL.
- ✅ 🟡 (hardening) `CartItemViewSet` покладався лише на queryset-scoping → додав `IsOwner` (belt-and-suspenders). +тест cart-isolation.
- ✅ 🟡 (hardening) `topProducts(limit)` без верхньої межі → cap `min(limit, 100)`.
- ⏭️ 🟡 GraphQL-інтроспекція в проді (леакає лише 3 імені полів; дані під staff-gate) — відкладено (тривіально, низька цінність).

### Результат
ruff/mypy чисті, pytest **86 passed**, coverage 95.24%.

---

## Цикл 3 — Веб UI / в'юхи / шаблони
Рев'ю: 1 субагент (усі шаблони + рендер в'юх), live-рендер усіх сторінок тест-клієнтом.

### Знахідки
- ✅ 🟠 Повідомлення review-флоу (success/error/info) ставились, але **ніде не показувались** (product_detail без loop, base без глобального) → користувач без зворотного зв'язку. Фікс: рендер `messages` глобально в `base.html`; прибрано локальні дублі в cart/order_detail.
- ✅ 🟡 Аналітика показувала raw-статуси (`pending`/`paid`) замість лейблів. Фікс: `orders_by_status` повертає `Status.label` (оновлено тест).
- ⏭️ 🟡 Seed без зображень — картки показують лого-плейсхолдер (фолбек працює; 12 фото є в `static/img/products/`, не підключені). Data/cosmetic, відкладено.
- Перевірено чистим: усі `{% url %}` резолвляться (11 сторінок → 200), `{% static %}` валідні, блоки збігаються з base, форми перерендерюються з помилками, empty-states, пагінація зберігає фільтри/сорт.

### Результат
ruff/mypy чисті, pytest **86 passed**, coverage 95.24%.

---

## Цикл 4 — API та цілісність даних
Рев'ю: 1 субагент (серіалізатори/viewsets/N+1/констрейнти/міграції), відтворення через APIClient.

### Знахідки
- ✅ 🟠 (HIGH) API-кошик приймав `quantity=0` (`PositiveIntegerField`→min 0 у DRF; веб захищений, API — ні) → "оплачене" замовлення на 0 грн із порожніми позиціями, що ще й рахувалось як покупка для відгуків. Фікс: `min_value=1` у `CartItemSerializer` + DB `CheckConstraint(quantity≥1)` на `CartItem`/`OrderItem` (міграція 0003). +тест.
- ⏭️ 🟡 `Order.user on_delete=CASCADE` (видалення юзера знищує історію замовлень) — дизайн-рішення; для прод-shop краще `PROTECT`/`SET_NULL`. Відкладено (нема вимоги зберігати замовлення після видалення акаунта).
- Перевірено чистим: N+1 (products/orders/cart/reviews мають select_related/prefetch), валідація (negative/huge qty, blank/missing contacts → 400), avg_rating null, коди 201/400/404/405, on_delete/unique_together/Decimal консистентні.

### Результат
ruff/mypy чисті, pytest **87 passed**, coverage 95.26%.

---

## Цикл 5 — Крос-катінг / консистентність / конфіг / тести
Рев'ю: 2 субагенти (config/Docker/CI + тести/мертвий код/консистентність).

### Знахідки
- ✅ 🟠 (MEDIUM) Завантажена media не віддавалась у прод-Docker (роут під DEBUG; WhiteNoise лише static; нема проксі) → фото товарів 404. Фікс: media-роут через `django.views.static.serve` у всіх середовищах (+коментар про nginx/CDN для реального проду).
- ✅ 🟠 (HIGH-тест) API-checkout oversell-rollback не покривався тестом. Фікс: +тест (stock=1, кошик 5 → 400, order/payment=0, кошик не очищено, stock незмінний).
- ✅ 🟡 Мертвий `CategorySerializer` (api) — видалено. Мертвий `static/js/main.js` (229 рядків, конфліктна клієнт-логіка) — видалено.
- ✅ 🟡 `SECURE_PROXY_SSL_HEADER` довірявся без проксі → env-gated (`USE_PROXY_SSL_HEADER`).
- ✅ 🟡 Нема docstrings на ключових view-класах (ТЗ) → додано (ProductListView/RegisterView/CheckoutView/AnalyticsDashboardView/OrderViewSet/ReviewCreateView).
- ✅ 🟡 `UnorderedObjectListWarning` у пагінації API-продуктів → явний `.order_by("-created_at")`.
- ✅ 🟡 CI-крок «lint + format» не перевіряв формат → перейменовано на «lint + isort» (чесно). Масовий `ruff format` (64 файли) НЕ застосовано — рестайл робочого коду поза surgical-changes.
- ⏭️ 🟡 review `IntegrityError`-гілка (гонка) без тесту — важко без concurrency-симуляції; БД-констрейнт гарантує цілісність. Відкладено.
- ⏭️ 🟡 `Order.user` CASCADE, `cart_update` stock==0 UX — дизайн/мінор, відкладено.
- Перевірено чистим: settings split, Docker (multi-stage/non-root/lock/entrypoint), `check --deploy`, `uv lock --check`, міграції, deps split, .gitignore/.env, owner-isolation/JWT/oversell тести змістовні, фабрики валідні, ruff F-rules чисто.

### Результат
ruff/mypy чисті, pytest **88 passed**, coverage 95.48%.

---

## Spec-gap перевірка (проти `docs/06 Project M3-1.md`)
Рев'ю: субагент змапив кожну вимогу ТЗ (§3–§10) на код.

### Закриті дірки
- ✅ 🔴 **M1** (§3.5, рубрика) Історія замовлень БЕЗ фільтрації → додав фільтр за статусом (`OrderListView` + форма в шаблоні). +тест.
- ✅ 🟠 **M2** (§3.1, рубрика) Нема сорту «за популярністю» → додав (web+API) через `Coalesce(Sum(order_items__quantity), 0)` (NULL-safe: без продажів = 0, не «зверху»). +тести.
- ✅ 🟡 P1 Вкладені категорії не демонструвались (seed flat) → seed створює дерево (`Ingredients → Hops/Malts/Yeast`). Тест оновлено (5 категорій).
- ✅ 🟡 P3 JWT-lifetimes не налаштовані/задокументовані → `SIMPLE_JWT` (access 30хв / refresh 1д / ротація) + нотатка в README.
- ⏭️ 🟡 P2 email лише console out-of-the-box (дворецепієнтна логіка коректна; SMTP через env) — прийнятно для навчального.
- ⏭️ 🟡 P4 «Залишити відгук» видно всім залогіненим (приховати = цикл products→reviews; серверний gate коректний, повідомлення тепер видиме) — лишаю.
- ⏭️ P5 адреси (опційні в ТЗ — правомірно пропущено), P6 профіль (вузький — ок).
- Решта ТЗ (§3.1–3.9, моделі §4, якість §6, чек-ліст §10, рубрика+бонуси §8) — ✅ покрито.

### Результат
ruff/mypy чисті, pytest **90 passed**, coverage 95.56%.

---

## Повний Playwright-прохід
Прокликано ключові флоу в браузері (dev-сервер). **Багів не знайдено — фікси не потрібні.**

- ✅ Каталог + сорт «популярність» (новий) — рендериться.
- ✅ Історія замовлень + фільтр за статусом (M1): `?status=cancelled` ховає оплачене → порожній список; дропдаун зі статусами.
- ✅ Показ повідомлень (фікс Циклу 3): review-флоу («лише після покупки») і cart («додано в кошик») — видимі.
- ✅ Логін buyer1, кошик (товар + сума + «Оформити»), add-to-cart.
- ✅ Swagger `/api/docs/`, GraphiQL `/graphql/` (у dev) — вантажаться.
- Регресія core-флоу (товар/checkout/оплата/відгук/admin-дашборд із попередніх юнітів) — без змін.

---

# Раунд 2 (повторний аудит) — фіксимо Medium+, Minor лише нотуємо

## R2 Цикл 1 — коректність/бізнес-логіка (адверсаріально + код аудиту-1)
Рев'ю: 1 адверсаріальний субагент, відтворення емпіричне.

- ✅ 🟠 (Important) API `ProductViewSet`: `avg_rating=Avg(reviews)` + `sold=Sum(order_items)` на одному запиті → **JOIN-множення** (sold × к-сть відгуків) → `?ordering=sold` бреше (bestseller програє менш-продаваному з відгуками). Фікс: `sold` через `Subquery` (avg лишився коректним). +тест. Web-сорт був чистий (нема avg-join).
- ⏭️ Minor (нотатка): `cancel_order` лишає `Payment.status=PAID` (revenue не зачеплено — фільтр за статусом замовлення); API payment `method` без валідації проти choices (data-quality; веб валідує).
- Перевірено чистим: deactivated-mid-checkout, web popularity, top_products, order-status-фільтр, CheckConstraint(qty≥1) на всіх шляхах, `Cart.__len__`, transaction-boundaries.

### Результат
ruff/mypy чисті, pytest **91 passed**, coverage 95.56%.

## R2 Цикл 2 — безпека/авторизація (+ новий media-роут, SIMPLE_JWT)
Рев'ю: 1 адверсаріальний субагент-безпека, відтворення емпіричне (replay-запити, path-traversal).

- ✅ 🟠 (Important) JWT refresh **replay**: `ROTATE_REFRESH_TOKENS=True`, але без `BLACKLIST_AFTER_ROTATION` і без застосунку `token_blacklist` → старий refresh лишався валідним до кінця TTL (1 день) навіть після ротації (відтворено: повтор старого refresh → 200). Фікс: додано `rest_framework_simplejwt.token_blacklist` в INSTALLED_APPS + `BLACKLIST_AFTER_ROTATION=True` + міграції. +тест (повтор старого refresh → 401).
- ✅ media-роут (`re_path … serve`) у всіх середовищах — перевірено на path-traversal: Django `safe_join` блокує `../`, відтворити не вдалося → **безпечно** (лишаємо).
- ⏭️ Minor (нотатка): prod HTTPS-хардненinг (`SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, HSTS) вимкнені за замовчуванням — прийнятно для навч-проєкту, вмикається через env у prod.
- ⏭️ Minor (нотатка): dev `SECRET_KEY` (default `dev-insecure-key-change-me`, 26 байт) дає `InsecureKeyLengthWarning` при HS256 — лише dev-дефолт, у prod ключ із env.
- Перевірено чистим: owner-isolation (order/cart 404 для чужого), read-only ProductViewSet (405 на запис), reviews лише після покупки (403), `IsOwner`, JWT-auth на захищених ендпоінтах.

### Результат
ruff/mypy чисті, pytest **92 passed**, coverage 95.56%.

## R2 Цикл 3 — веб UI/шаблони (+ order-filter, popularity, messages)
_(заповнюється)_

## R2 Цикл 4 — API/цілісність (+ sold-ordering, CheckConstraint, міграція 0003)
_(заповнюється)_

## R2 Цикл 5 — крос-катінг/перф/консистентність/тести
_(заповнюється)_
