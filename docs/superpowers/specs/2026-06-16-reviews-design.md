# Дизайн: апка `reviews` (відгуки після покупки)

> Юніт 5. Загальний дизайн §3.2. Рішення автономні. Спека з вбудованим планом.

## Межі
**У межах:** `Review` (rating 1-5, comment, unique product+user), форма+сторінка створення (лише після покупки, один раз), показ відгуків + середній рейтинг на детальній товару.
**Поза межами:** редагування/видалення відгуків, голосування «корисно», модерація.

## Залежності (ациклічно)
`reviews → products, orders, users`. **products НЕ імпортує reviews** — детальна показує відгуки через reverse-accessor `product.reviews` та `Avg` (без import), а форма відгуку — на окремій сторінці апки `reviews`. Так уникаємо циклу.

## Модель `reviews.Review`
`product`(FK Product, CASCADE, `related_name="reviews"`), `user`(FK AUTH_USER_MODEL, CASCADE, `related_name="reviews"`), `rating`(PositiveSmallInt, валідатори 1-5), `comment`(Text, blank), `created_at`. `Meta`: `unique_together=("product","user")`, ordering `-created_at`. `__str__`→`{rating}★ {product}`.

## Логіка (`reviews/services.py`)
- `has_purchased(user, product) -> bool`: існує `OrderItem` з `order__user=user`, `order__status ∈ {paid,shipped,delivered}`, `product=product`.
- `can_review(user, product) -> bool`: `has_purchased` **і** ще немає відгуку від цього user на цей product.

## В'юха/URL
- `ReviewCreateView(LoginRequiredMixin)` на `/product/<slug>/review/`: GET — форма, якщо `can_review` (інакше message+redirect на товар); POST — валідація `can_review` + `ReviewForm` → створити Review → redirect на товар.
- `ReviewForm(ModelForm)`: rating (Select 1-5), comment.
- `reviews.urls` (app_name="reviews") включити в config на "".

## Детальна товару (products, БЕЗ import reviews)
`ProductDetailView.get_context_data` додає `reviews = product.reviews.select_related("user")` та `avg_rating` (`Avg("rating")`). Шаблон: список `.review-card` + середній рейтинг + лінк «Залишити відгук» (для залогінених) → `reviews:create`.

## Тести (TDD = критерії)
- `has_purchased`/`can_review`: купив→True; не купив→False; уже залишив→False.
- review create: не-покупець → відгук не створено (redirect); покупець → створено.
- дубль відгуку заблоковано.
- відгук показується на детальній; середній рейтинг рахується.

## Browser-verify
Залогінитись покупцем (з юніту orders уже є замовлення buyer1) → /product/<slug>/review/ → лишити відгук → відгук видно на детальній із рейтингом. Скріншот.

## План (staged)
1. Модель + міграція + admin + factory + тести моделі.
2. services (`has_purchased`/`can_review`) + тести.
3. ReviewForm + ReviewCreateView + url + template + тести.
4. Детальна: context (reviews+avg) + шаблон + тест показу.
5. Browser-verify.
