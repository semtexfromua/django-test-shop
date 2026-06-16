# Дизайн: admin-аналітика

> Юніт 7. Загальний дизайн §3.6. Рішення автономні.

## Межі
**У межах:** агрегації/анотації (виторг, к-сть замовлень за статусами, топ-товари за продажами), custom admin actions (відправлено/доставлено/скасувати+повернення stock), staff-дашборд, ролі (група Managers). 
**Поза межами:** графіки/чарти, експорт.

## Аналітика (`orders/analytics.py`) — чисті функції-агрегації
- `total_revenue()` → `Sum(total_price)` по замовленнях зі статусом paid/shipped/delivered.
- `order_count()`, `orders_by_status()` → `Count` згруповано.
- `top_products(limit=5)` → `OrderItem` `annotate(sold=Sum(quantity))` згруповано по товару, сортування за продажами.

## Сервіс
`orders/services.py::cancel_order(order)` — у `atomic` повертає stock по items, статус `cancelled` (лише якщо не cancelled).

## Admin
- `OrderAdmin` actions: `mark_shipped`, `mark_delivered`, `cancel_orders` (через `cancel_order`).
- `ProductAdmin`: у changelist `annotate(sold)` + колонка/сортування «продано».

## Дашборд
`AnalyticsDashboardView` (staff-only, `UserPassesTestMixin` is_staff) на `/orders/analytics/` + шаблон: виторг, к-сть за статусами, топ-товари. Доступ нестафу → редірект на login.

## Ролі
Команда `setup_roles` — група `Managers` з правами на orders (view/change Order).

## Тести
- analytics: revenue лише оплачені; top_products рахує продані; counts.
- cancel_order повертає stock + статус cancelled.
- dashboard: staff→200, не-staff→302/403.
- setup_roles: створює групу Managers (ідемпотентно).

## Browser-verify
Зайти суперюзером → /orders/analytics/ → бачити виторг/статуси/топ-товари. Скріншот.
