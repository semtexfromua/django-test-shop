<div align="center">

# 🍺 Hop & Barley

**Повноцінний інтернет-магазин інгредієнтів для домашнього пивоваріння — веб-інтерфейс на Django + REST API на DRF + GraphQL-аналітика, на PostgreSQL та Docker.**

[![CI](https://github.com/semtexfromua/django-test-shop/actions/workflows/ci.yml/badge.svg)](https://github.com/semtexfromua/django-test-shop/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.13-blue)
![Django](https://img.shields.io/badge/Django-5.2-092E20)
![DRF](https://img.shields.io/badge/DRF-3.17-A30000)
![Coverage](https://img.shields.io/badge/coverage-95%25-brightgreen)
![Ruff](https://img.shields.io/badge/lint-ruff-261230)
![mypy](https://img.shields.io/badge/types-mypy-2A6DB2)

[English](README.md) · **Українська**

<img src="docs/screenshots/catalog.jpg" alt="Каталог Hop & Barley" width="80%">

</div>

---

## Зміст

- [Огляд](#огляд)
- [Можливості](#можливості)
- [Скріншоти](#скріншоти)
- [Стек](#стек)
- [Швидкий старт (Docker)](#швидкий-старт-docker)
- [Локальна розробка](#локальна-розробка)
- [REST API та JWT](#rest-api-та-jwt)
- [GraphQL (бонус)](#graphql-бонус)
- [Тести та якість коду](#тести-та-якість-коду)
- [Структура проєкту](#структура-проєкту)
- [Чек-ліст реалізації](#чек-ліст-реалізації)
- [Ліцензія](#ліцензія)

## Огляд

**Hop & Barley** перетворює статичний HTML/CSS-шаблон на робочий інтернет-магазин інгредієнтів для
пивоваріння (хміль, солод, дріжджі, набори). Це навчальний проєкт, що демонструє ідіоматичний Django,
Django REST Framework, моделювання реляційних даних та інфраструктуру, наближену до продакшену.

Дві точки входу поверх однієї доменної моделі:

- **Веб-вітрина** — серверний рендеринг шаблонів Django, автентифікація через **сесії** та **кошик у сесії**.
- **REST API** — DRF з **JWT**-авторизацією та кошиком у БД (`Cart`/`CartItem`), для зовнішніх клієнтів.

Бізнес-логіка винесена з тонких в'юх у `services.py` кожної апки. Checkout виконується в межах
`transaction.atomic` із блокуванням рядків `select_for_update` (без оверселлу), знімає ціну в
`OrderItem` і після коміту надсилає email покупцю та адміну.

## Можливості

- **Каталог і пошук** — пагінація, фільтри за категорією та діапазоном цін, пошук за назвою/описом, сортування за ціною / популярністю / новизною. Вкладені категорії (`Ingredients → Hops/Malts/Yeast`).
- **Сторінка товару** — зображення, опис, ціна, середній рейтинг, відгуки; додавання в кошик з кількістю. Відгук можна лишити **лише після покупки**, один на товар від користувача.
- **Кошик** — у сесії; додати / змінити / видалити, живий підрахунок суми, **перевірка залишків**.
- **Оформлення** — форма контактів і доставки, мок-оплата, атомарне створення замовлення зі **знімком ціни**, **без оверселлу**, та **email-сповіщення** покупцю + адміну.
- **Кабінет** — реєстрація, вхід/вихід, **історія замовлень з фільтром за статусом**, редагування профілю, зміна пароля. Унікальність email.
- **Адмінка та аналітика** — Django-адмінка для всіх моделей з пошуком, фільтрами та кастомними діями (відправити/доставити, скасувати → повернути залишок); staff-дашборд аналітики (виторг, кількість замовлень, розподіл за статусами, топ-товари) на ORM-агрегаціях.
- **REST API** — товари, кошик, замовлення, відгуки, реєстрація; JWT access/refresh з **ротацією + чорним списком**; object-level права власника; Swagger/OpenAPI.
- **GraphQL-аналітика (бонус)** — єдиний ендпоінт `/graphql/`, резолвери лише для персоналу; introspection вимкнено у проді.
- **Якість** — анотації типів + докстрінги (`mypy` чисто), лінт `ruff`, **покриття тестами 95%+** через `pytest`, Docker Compose і CI на GitHub Actions.

## Скріншоти

### Вітрина

| Каталог | Товар і відгуки |
|---|---|
| [![Каталог](docs/screenshots/catalog.jpg)](docs/screenshots/catalog.jpg) | [![Товар](docs/screenshots/product-detail.jpg)](docs/screenshots/product-detail.jpg) |

| Кошик | Оформлення | Історія замовлень |
|---|---|---|
| [![Кошик](docs/screenshots/cart.png)](docs/screenshots/cart.png) | [![Оформлення](docs/screenshots/checkout.png)](docs/screenshots/checkout.png) | [![Замовлення](docs/screenshots/order-history.png)](docs/screenshots/order-history.png) |

### Адмінка та API

| Дашборд аналітики | Swagger / OpenAPI | GraphiQL |
|---|---|---|
| [![Аналітика](docs/screenshots/analytics.png)](docs/screenshots/analytics.png) | [![Swagger](docs/screenshots/api-docs.png)](docs/screenshots/api-docs.png) | [![GraphiQL](docs/screenshots/graphiql.png)](docs/screenshots/graphiql.png) |

## Стек

| Сфера | Інструменти |
|---|---|
| Ядро | Django 5.2, Python 3.13 |
| API | Django REST Framework · SimpleJWT · drf-spectacular (OpenAPI) · django-filter |
| GraphQL | graphene-django |
| База даних | PostgreSQL 16 (psycopg 3) |
| Інфра | Docker та Docker Compose · Gunicorn · WhiteNoise |
| Тулінг | uv (залежності) · ruff (лінт/isort) · mypy (+django-stubs) · pytest-django · factory-boy · pytest-cov |
| CI | GitHub Actions (ruff + mypy + pytest, збірка Docker-образу) |

## Швидкий старт (Docker)

> Потрібні Docker та Docker Compose. Піднімає застосунок + PostgreSQL.

```bash
cp .env.example .env
docker compose up --build
```

| Сторінка | URL |
|---|---|
| Вітрина | http://localhost:8000/ |
| Адмінка | http://localhost:8000/admin/ |
| Swagger (REST) | http://localhost:8000/api/docs/ |
| GraphiQL | http://localhost:8000/graphql/ |

Демо-дані (каталог із зображеннями та вкладеними категоріями), адмін, роль Managers:

```bash
docker compose run --rm web python manage.py seed_catalog
docker compose run --rm web python manage.py createsuperuser
docker compose run --rm web python manage.py setup_roles   # група «Managers»
```

> **Примітка:** `docker-compose.yml` містить демо-дефолти (пароль БД, `SECRET_KEY`) для запуску
> однією командою. Для реального деплою обов'язково перевизначте `SECRET_KEY` і креденшіали БД через
> оточення та увімкніть HTTPS-прапори (`SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `SECURE_HSTS_SECONDS`).

## Локальна розробка

```bash
uv sync                                   # встановити залежності (з dev-групою)
docker compose up -d db                   # PostgreSQL на localhost:5433 (5432 часто зайнятий)
uv run python manage.py migrate
uv run python manage.py seed_catalog
uv run python manage.py runserver         # http://127.0.0.1:8000/  (DEBUG=True)
```

## REST API та JWT

API використовує **JWT**: після входу отримуєте `access` (30 хв) та `refresh` (1 день); refresh
**ротується** при використанні, а старий потрапляє в **чорний список**. Надсилайте
`Authorization: Bearer <access>`.

```bash
# 1) Реєстрація
curl -X POST localhost:8000/api/users/register/ \
  -H 'Content-Type: application/json' \
  -d '{"username":"alice","email":"alice@example.com","password":"Br3wMaster!99"}'

# 2) Вхід → access / refresh токени
curl -X POST localhost:8000/api/users/login/ \
  -H 'Content-Type: application/json' \
  -d '{"username":"alice","password":"Br3wMaster!99"}'
# → {"access":"<JWT>","refresh":"<JWT>"}

# 3) Каталог (публічно; фільтр / пошук / сортування)
curl 'localhost:8000/api/products/?search=cascade&ordering=-sold'

# 4) Додати в кошик і створити замовлення (з токеном)
curl -X POST localhost:8000/api/cart/ \
  -H 'Authorization: Bearer <access>' -H 'Content-Type: application/json' \
  -d '{"product":1,"quantity":2}'
curl -X POST localhost:8000/api/orders/ \
  -H 'Authorization: Bearer <access>' -H 'Content-Type: application/json' \
  -d '{"full_name":"Alice","email":"alice@example.com","phone":"+380...","shipping_address":"...","method":"card"}'

# 5) Оновити access за refresh
curl -X POST localhost:8000/api/users/refresh/ \
  -H 'Content-Type: application/json' -d '{"refresh":"<refresh>"}'
```

| Ресурс | Метод | Ендпоінт |
|---|---|---|
| Товари | `GET` | `/api/products/`, `/api/products/{id}/` |
| Відгуки | `GET` `POST` | `/api/products/{id}/reviews/` |
| Кошик | `GET` `POST` `PATCH` `DELETE` | `/api/cart/`, `/api/cart/{id}/` |
| Замовлення | `GET` `POST` | `/api/orders/`, `/api/orders/{id}/` (лише свої) |
| Реєстрація | `POST` | `/api/users/register/` |
| Вхід / Refresh | `POST` | `/api/users/login/`, `/api/users/refresh/` |
| Документація | `GET` | `/api/docs/` (Swagger), `/api/schema/` (OpenAPI 3) |

Права — object-level: користувач бачить і змінює лише свій кошик та свої замовлення.
Повні схеми запитів/відповідей — у **Swagger** за `/api/docs/`.

## GraphQL (бонус)

Єдиний ендпоінт `POST /graphql/` (GraphiQL UI у dev). Резолвери аналітики — **лише для персоналу**:

```graphql
{
  revenue
  orderCount
  topProducts(limit: 5) { name sold }
}
```

## Тести та якість коду

```bash
uv run pytest          # тести + поріг покриття (падає нижче 80%); зараз ~95%
uv run ruff check .    # лінт + сортування імпортів
uv run mypy .          # статична перевірка типів
```

CI (GitHub Actions) запускає всі три на кожен push у `main`/`develop` та на PR, плюс збірку
Docker-образу.

## Структура проєкту

```
config/      налаштування (base/dev/prod), кореневі urls, wsgi/asgi
users/       кастомний User, автентифікація, кабінет (через сесії)
products/    Category, Product, в'юхи каталогу, команда seed_catalog
reviews/     відгуки (лише після покупки, один на товар/користувача)
orders/      кошик у сесії + Cart/CartItem (API), checkout, services, аналітика, дії адмінки
payments/    мок-сервіс оплати
api/         DRF: серіалізатори, viewsets, JWT, OpenAPI
gql/         GraphQL-схема та резолвери (аналітика)
templates/   Django-шаблони (дизайн Hop & Barley)
static/      CSS, зображення, іконки
docs/        ТЗ, дизайн-документи, лог аудиту, скріншоти
```

Залежності ациклічні: `users, products → orders → payments`; `reviews → products, orders`;
`api, gql → усі`. Бізнес-логіка — у `<app>/services.py`; в'юхи лишаються тонкими.

## Чек-ліст реалізації

- [x] `docker compose up` піднімає весь стек на PostgreSQL
- [x] Каталог: фільтри, пошук, пагінація, сортування (зокрема за популярністю)
- [x] Сторінка товару: деталі, відгуки, додавання в кошик
- [x] Кошик: керування вмістом, підрахунок суми, перевірка залишків
- [x] Оформлення: створення замовлення, email-сповіщення, валідація, atomic + знімок ціни
- [x] Кабінет: реєстрація, вхід, історія замовлень (з фільтром за статусом), профіль, зміна пароля
- [x] REST API: JWT (access/refresh + ротація/blacklist), object-level права, Swagger
- [x] Адмінка: аналітика, фільтри, кастомні дії, налаштування ролей
- [x] Анотації типів + докстрінги · `ruff`/`mypy` чисто · тести (покриття ≥ 80%, ~95%)
- [x] Змістовні коміти · гілки `feature/* → develop → main`
- [x] **Бонус:** GraphQL-аналітика · CI на GitHub Actions · менеджер залежностей `uv`

## Ліцензія

Навчальний проєкт — без окремої ліцензії. HTML/CSS-дизайн Hop & Barley походить з
[MagicCodeGit/Hop-and-Barley](https://github.com/MagicCodeGit/Hop-and-Barley).
