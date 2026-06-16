# Hop & Barley — інтернет-магазин (Django/DRF)

Навчальний проєкт: магазин пивоварних інгредієнтів із **веб-інтерфейсом** (Django + сесії)
та **REST API** (DRF + JWT), на PostgreSQL у Docker. Бонусом — **GraphQL**-аналітика та CI.

ТЗ: `docs/06 Project M3-1.md` · дизайн-документи: `docs/superpowers/specs/`.

## Стек
Django 5.2 · DRF · SimpleJWT · drf-spectacular · django-filter · graphene-django ·
PostgreSQL 16 · Docker · uv · ruff · mypy · pytest (coverage ≥80%).

## Швидкий старт (Docker)
```bash
cp .env.example .env
docker compose up --build
```
- Магазин: http://localhost:8000/
- Адмінка: http://localhost:8000/admin/
- Swagger (REST): http://localhost:8000/api/docs/
- GraphiQL: http://localhost:8000/graphql/

Демо-дані та суперюзер:
```bash
docker compose run --rm web python manage.py seed_catalog
docker compose run --rm web python manage.py createsuperuser
docker compose run --rm web python manage.py setup_roles   # група Managers
```

## Локальна розробка
```bash
uv sync
docker compose up -d db          # Postgres на localhost:5433 (5432 часто зайнятий)
uv run python manage.py migrate
uv run python manage.py seed_catalog
uv run python manage.py runserver
```

## Тести, лінтери, типи
```bash
uv run pytest            # тести + поріг покриття ≥80%
uv run ruff check .      # лінт + сортування імпортів
uv run mypy .            # перевірка типів
```

## REST API (JWT)
```bash
# 1) Реєстрація
curl -X POST localhost:8000/api/users/register/ \
  -H 'Content-Type: application/json' \
  -d '{"username":"alice","email":"a@e.com","password":"Str0ngPwd!23"}'

# 2) Логін → access/refresh токени
curl -X POST localhost:8000/api/users/login/ \
  -H 'Content-Type: application/json' \
  -d '{"username":"alice","password":"Str0ngPwd!23"}'
# → {"access":"<JWT>","refresh":"<JWT>"}

# 3) Каталог (публічно, з фільтрами/пошуком/сортуванням)
curl 'localhost:8000/api/products/?search=cascade&ordering=price'

# 4) Кошик і замовлення (з токеном)
curl -X POST localhost:8000/api/cart/ -H 'Authorization: Bearer <access>' \
  -H 'Content-Type: application/json' -d '{"product":1,"quantity":2}'
curl -X POST localhost:8000/api/orders/ -H 'Authorization: Bearer <access>' \
  -H 'Content-Type: application/json' \
  -d '{"full_name":"Alice","email":"a@e.com","phone":"+380...","shipping_address":"...","method":"card"}'

# 5) Оновлення access за refresh
curl -X POST localhost:8000/api/users/refresh/ \
  -H 'Content-Type: application/json' -d '{"refresh":"<refresh>"}'
```
**Токени:** access живе 30 хв, refresh — 1 день; при оновленні refresh ротується. Повна схема — `/api/docs/` (Swagger) та `/api/schema/` (OpenAPI 3).

## GraphQL (бонус, аналітика — лише для персоналу)
`POST /graphql/` (або GraphiQL у браузері):
```graphql
{ revenue orderCount topProducts(limit: 5) { name sold } }
```

## Ключова бізнес-логіка
- **Кошик:** веб — у сесії; API — модель `CartItem`.
- **Checkout:** `transaction.atomic` + `select_for_update` → перевірка залишків (без оверселлу),
  знімок цін у `OrderItem`, мок-оплата, email юзеру+адміну.
- **Відгуки:** лише після покупки (оплачене/доставлене замовлення), один на товар.
- **Аналітика:** агрегації (виторг, топ-товари, статуси) у staff-дашборді `/orders/analytics/`.

## Структура
```
config/    налаштування (base/dev/prod), urls
users/     кастомний User, автентифікація, кабінет
products/  Category, Product, каталог
reviews/   відгуки (після покупки)
orders/    кошик, замовлення, checkout, аналітика
payments/  мок-оплата
api/        REST API (DRF + JWT + OpenAPI)
gql/        GraphQL-аналітика
templates/ static/   шаблони й статика (Hop & Barley)
```

## Чек-ліст реалізації
- [x] `docker compose up` піднімає все · PostgreSQL
- [x] Каталог: фільтри, пошук, пагінація · сторінка товару + відгуки + кошик
- [x] Кошик + перевірка залишків · checkout (замовлення, email, валідація)
- [x] Кабінет: реєстрація, вхід, історія, профіль, зміна пароля
- [x] REST API + JWT + права + Swagger
- [x] Адмінка з аналітикою, фільтрами, діями, ролями
- [x] Типізація + докстрінги · ruff/mypy без помилок · тести (coverage ≥80%)
- [x] Бонуси: GraphQL, CI (GitHub Actions), покриття ≥80%
- [x] README · змістовні коміти · гілки `feature/* → develop → main`
