# Дизайн: Інтернет-магазин на Django/DRF

> Дизайн-документ до ТЗ `docs/06 Project M3-1.md`. Затверджено 2026-06-16.
> Режим роботи: код пише асистент, користувач рев'ює і вчиться на готовому.
> Це **загальна** спека (умбрела). Деталізація — окремий брейншторм + спека на кожну апку
> під час реалізації, цикл: **brainstorm → spec → plan → TDD → completion**. Не все відразу.

## 1. Огляд

Двоголовий застосунок:
- **Веб** — Django CBV + шаблони, **session auth**, кошик у сесії.
- **REST API** (`/api/`) — DRF + **JWT** (access/refresh), кошик у БД.
- **Бонуси** (усі 3): GraphQL-аналітика, CI/CD, покриття тестами ≥80%.

Інфраструктура: **PostgreSQL** + **Docker Compose**. Менеджер залежностей: **uv**.
HTML-основа: https://github.com/MagicCodeGit/Hop-and-Barley.git (статика → Django-шаблони).

## 2. Стек

| Шар | Вибір |
|---|---|
| Framework | Django 5.x, Python 3.12+ |
| API | DRF, `djangorestframework-simplejwt`, `django-filter`, `drf-spectacular` |
| БД | PostgreSQL 16, `psycopg` (v3) |
| Зображення | Pillow |
| Якість | `ruff` (lint+format+isort), `mypy` + `django-stubs` + `djangorestframework-stubs` |
| Тести | `pytest-django`, `pytest-cov`, `factory_boy` |
| Конфіг | `django-environ` (`.env`) |
| Статика | WhiteNoise |
| Деплой | Docker (multi-stage, uv), docker-compose, gunicorn |
| Бонус | `graphene-django`, GitHub Actions |

Свідомо **не** беремо: Celery/Redis, реальні платіжні шлюзи, мікросервіси — не потрібні для ТЗ.

## 3. Структура застосунків

Плоска (апки в корені + `config/`) — для 6 апок `apps/`-контейнер додає тертя без виграшу.

```
config/      # settings (base/dev/prod), urls, asgi/wsgi
users/       # кастомний User (AbstractUser), auth, профіль
products/    # Category, Product (каталог)
reviews/     # Review (окремо — інакше цикл products↔orders)
orders/      # Order, OrderItem, Cart, CartItem, сесійний кошик, checkout, services
payments/    # Payment (мок) + process_payment()
api/         # DRF router, JWT, drf-spectacular
graphql/     # бонус
templates/   static/   media/
```

**Граф залежностей (ациклічний):**
```
users, products  →  orders  →  payments
                  ↘         ↘
                    reviews (→ products, orders)
api / graphql → усі
```

Тести — **по-апково** (`products/tests/…`), не глобальна `tests/`.

## 4. Моделі даних

**users.User(AbstractUser)** — кастомний з 1-го дня (пізніше міняти боляче). Без зайвих полів.

**products.Category**: `name`, `slug`(unique), `parent`(self-FK, null) — дерево, `created_at`, `updated_at`.

**products.Product**: `name`, `slug`(unique), `description`, `price`(Decimal), `category`(FK), `image`(ImageField), `is_active`(bool), `stock`(int), `created_at`, `updated_at`.
- Сортування «за популярністю» — `annotate` к-стю проданих одиниць (через `OrderItem`), без денормалізації.

**reviews.Review**: `product`(FK), `user`(FK), `rating`(int 1–5, валідатори), `comment`(Text), `created_at`. `unique(product, user)`.

**orders.Cart**: `user`(OneToOne), `created_at`, `updated_at`.
**orders.CartItem**: `cart`(FK), `product`(FK), `quantity`(int>0). `unique(cart, product)`.

**orders.Order**: `user`(FK), `status`(pending/paid/shipped/delivered/cancelled), `total_price`(Decimal), контактні дані (`full_name`, `email`, `phone`), `shipping_address`(Text), `created_at`, `updated_at`.

**orders.OrderItem**: `order`(FK), `product`(FK, `PROTECT` — зберегти історію), `quantity`(int), `price`(Decimal — **знімок ціни**).

**payments.Payment**: `order`(OneToOne), `method`(choices, мок), `status`(pending/paid/failed), `amount`(Decimal), `transaction_id`(мок), `created_at`.

## 5. Кошик і checkout (ядро бізнес-логіки)

- **Веб:** кошик у `request.session`, інкапсульований у `CartService` (додати/змінити/видалити/підсумок).
- **API:** `Cart`/`CartItem` у БД, прив'язані до JWT-юзера.
- **Спільне ядро** `orders/services.py::create_order(user, items, contact) -> Order`:
  1. валідація: кошик не порожній;
  2. `transaction.atomic` + `select_for_update` на товарах → перевірка `qty ≤ stock`;
  3. створення `Order`(pending) + `OrderItem` (знімок ціни), підрахунок `total`;
  4. списання `stock`;
  5. `payments.process_payment(order, method)` (мок→success) → `Order.status = paid`;
  6. очистка кошика;
  7. email юзеру + адміну через `transaction.on_commit`.
- **Оркестрація** (order + payment) — у в'юсі/viewset в одному `atomic`; `orders` не залежить від `payments`.
- Скасування замовлення (`cancelled`) → повертає `stock`.

**Тести (обов'язково):** оверселл, порожній кошик, паралельні замовлення (race на stock), знімок ціни.

## 6. Авторизація і доступ

- **Веб:** Django session auth; `LoginRequiredMixin` на `/account/`, `/checkout/`.
- **API:** SimpleJWT (access+refresh); `IsAuthenticated` + object-level `IsOwner` (замовлення/кошик — лише своє); `products` — read-only публічно.
- **Відгук:** дозволено лише якщо в юзера є `paid`/`delivered` замовлення з цим товаром (перевірка в serializer/form). `unique(product, user)`.
- Ролі в адмінці: групи `staff`/`manager` з різними правами.

## 7. Веб-сторінки

`/` та `/products/` (каталог: фільтри категорія/ціна, пошук name+description, сортування, пагінація) · `/product/<slug>/` (деталі, відгуки, додати в кошик) · `/cart/` · `/checkout/` · `/account/` (реєстрація, вхід/вихід, історія+фільтр, профіль, зміна пароля) · `/admin/`.

## 8. REST API (`/api/`)

| Ресурс | URL | Методи |
|---|---|---|
| Products | `/api/products/`, `/api/products/<id>/` | GET (фільтри/пошук/сорт/пагінація) |
| Orders | `/api/orders/`, `/api/orders/<id>/` | GET/POST/PATCH/PUT/DELETE (лише свої) |
| Users | `/api/users/register/`, `/api/users/login/`, refresh | POST |
| Cart | `/api/cart/` | GET/POST/PATCH/DELETE |
| Reviews | `/api/products/<id>/reviews/` | GET/POST |

- ViewSets + routers; серіалізатори/viewsets — у відповідних апках, агрегація роутів у `api/`.
- Фільтрація: `django-filter` + `SearchFilter` + `OrderingFilter`.
- OpenAPI: `drf-spectacular` на `/api/docs/`.

## 9. Якість та інфраструктура

- **Типізація + докстрінги** на публічних API/важливих модулях; `mypy` (django-stubs, drf-stubs).
- **Лінт:** `ruff` (lint + format + isort). **pre-commit:** ruff, ruff-format, mypy.
- **Тести:** `pytest-django` + `factory_boy`; `pytest-cov` із порогом **≥80%**.
- **Конфіг:** `config/settings/{base,dev,prod}.py`; секрети з env (`SECRET_KEY`, `DEBUG`, БД, `EMAIL_*`, `ALLOWED_HOSTS`); `.env.example` у репо.
- **Email:** console backend у dev, SMTP у prod (з env).
- **Docker:** multi-stage Dockerfile (uv); `docker-compose` (web + `postgres:16` з healthcheck, volume `pgdata`, `media`, `static`); entrypoint `migrate → collectstatic → gunicorn`; `.dockerignore`.
- **Git:** `feature/…` → `develop` → `main`; змістовні невеликі коміти. (Репо ініціалізуємо першим кроком.)

## 10. Бонуси (тиждень 3)

- **CI (GitHub Actions):** ruff + mypy + pytest (з postgres service, coverage) + build образу — на push/PR.
- **Coverage ≥80%:** поріг у `pytest-cov`.
- **GraphQL:** `graphene-django`, ендпоінт `/graphql/`; аналітика (виторг, к-сть замовлень, середній чек, тренди, топ-товари, залишки, повторні покупки) з авторизацією.

## 11. Порядок збірки (по тижнях)

**Тиждень 1 — фундамент і каталог**
1. Init: `uv` + Django + `config/settings` split + Docker + Postgres + ruff/mypy/pytest baseline + `git init`.
2. Кастомний `User`; підключення шаблону Hop-and-Barley + статика (WhiteNoise).
3. Моделі (`Category`, `Product`, `Review`, `Cart`, `CartItem`, `Order`, `OrderItem`, `Payment`) + міграції + admin baseline + factories.
4. Каталог: список, фільтри, пошук, сортування, пагінація. **+ тести.**

**Тиждень 2 — магазин**
5. Сторінка товару + відгуки (правило «після покупки»).
6. Сесійний кошик (`CartService`) + перевірка залишків.
7. Checkout: форма, мок-оплата, атомарне замовлення, email. **+ тести.**
8. Кабінет: реєстрація, вхід/вихід, історія замовлень (+фільтр), профіль, зміна пароля.

**Тиждень 3 — API, якість, бонуси**
9. Адмінка: агрегації/аналітика, фільтри, custom actions, ролі.
10. REST API: усі ендпоінти, JWT, permissions, `drf-spectacular`. **+ тести.**
11. Якісний прохід: типізація, mypy, ruff, coverage ≥80%; README.
12. Бонуси: CI, GraphQL. Фінальна перевірка за чек-лістом ТЗ.

## 12. Критерії готовності (з ТЗ)

`docker-compose up` піднімає все на чистій системі · PostgreSQL · каталог (фільтри/пошук/пагінація) · товар+відгуки+кошик · checkout (замовлення+email+валідація) · кабінет · REST API (JWT, права, docs) · адмінка з аналітикою · Swagger працює · типізація+докстрінги · ruff/mypy без критичних · тести проходять · README повний · змістовні коміти/гілки.
