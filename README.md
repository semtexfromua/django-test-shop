# Інтернет-магазин (Django/DRF)

Навчальний проєкт: інтернет-магазин із веб-інтерфейсом (Django + сесії) та REST API (DRF + JWT).
ТЗ — `docs/06 Project M3-1.md`; загальний дизайн — `docs/superpowers/specs/`.

## Стек
Django 5.2 · PostgreSQL 16 · Docker · uv · ruff · mypy · pytest.

## Запуск через Docker
```bash
cp .env.example .env
docker compose up --build
```
Застосунок: http://localhost:8000 · Адмінка: http://localhost:8000/admin/

## Локальна розробка
```bash
uv sync
docker compose up -d db                 # Postgres на localhost:5432
uv run python manage.py migrate
uv run python manage.py runserver
```

## Тести та якість коду
```bash
uv run pytest
uv run ruff check .
uv run mypy .
```

## Структура
`config/` — налаштування · `users/` — користувачі. Далі за дорожньою картою:
`products/ reviews/ orders/ payments/ api/ graphql/`.

> Проєкт у процесі реалізації по тижнях згідно з дорожньою картою ТЗ.
