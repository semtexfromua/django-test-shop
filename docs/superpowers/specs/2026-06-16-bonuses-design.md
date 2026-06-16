# Дизайн: бонуси (coverage ≥80%, CI, GraphQL, README)

> Юніт 8 (фінальний). Загальний дизайн §10. Рішення автономні.

## 1. Coverage ≥80%
Увімкнути `[tool.coverage.report] fail_under = 80` у pyproject (зараз ~95%). pytest падає, якщо нижче.

## 2. CI (GitHub Actions)
`.github/workflows/ci.yml`: на push/PR — postgres-service, `uv sync`, `ruff check`, `mypy`, `pytest`, збірка Docker-образу. (Не запускається тут — артефакт для GitHub.)

## 3. GraphQL-аналітика (бонус)
`gql/` app (НЕ `graphql` — щоб не затінити пакет graphql-core), `graphene-django`. Ендпоінт `/graphql/`. Query: `revenue`, `orderCount`, `topProducts(limit)` — перевикористовують `orders.analytics`. Доступ лише staff (резолвери перевіряють `info.context.user.is_staff`, інакше `GraphQLError`). settings: `graphene_django` + `GRAPHENE={"SCHEMA": "gql.schema.schema"}`. mypy: ignore graphene*.

## 4. README
Повний README: опис, запуск (Docker), приклади API з JWT (register/login/cart/order), GraphQL, тести/лінтери, структура, чек-ліст.

## Тести
- GraphQL: staff-запит revenue → значення; не-staff → помилка/нуль.
- coverage-gate перевіряється самим pytest.

## Browser-verify
GraphiQL `/graphql/` відкривається. Скріншот.
