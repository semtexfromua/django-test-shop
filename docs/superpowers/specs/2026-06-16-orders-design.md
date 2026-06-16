# Дизайн: `orders` + `payments` (кошик, checkout, оплата-мок)

> Юніти 4-5 разом (checkout оркеструє order+payment). Загальний дизайн §3.3, §3.4, §4.
> Рішення автономні.

## Межі
**У межах:** `orders/` (Order, OrderItem, сесійний кошик `CartService`, checkout, `services.create_order`, історія замовлень), `payments/` (Payment-мок + `process_payment`). Add-to-cart оживлено.
**Поза межами:** DB-кошик `Cart`/`CartItem` (для API — юніт API), реальні платіжні шлюзи/вебхуки, нагадування.

## Моделі

### orders.Order
`user`(FK `settings.AUTH_USER_MODEL`, `related_name="orders"`), `status`(choices pending/paid/shipped/delivered/cancelled, default pending), `total_price`(Decimal 10,2), `full_name`(Char), `email`(Email), `phone`(Char), `shipping_address`(Text), `created_at/updated_at`. Meta ordering `-created_at`. `__str__`→`Замовлення #{pk}`. FK через `AUTH_USER_MODEL` рядком — без import users (уникаємо циклу).

### orders.OrderItem
`order`(FK `related_name="items"`), `product`(FK Product, `PROTECT`), `quantity`(PositiveInt), `price`(Decimal — **знімок**). `subtotal` property = price*quantity.

### payments.Payment
`order`(OneToOne Order, `related_name="payment"`), `method`(choices card/cash, мок), `status`(pending/paid/failed, default pending), `amount`(Decimal), `transaction_id`(Char blank), `created_at`. FK→orders (payments залежить від orders).

## Сесійний кошик — `orders/cart.py::Cart`
- Зберігання: `session["cart"] = {product_id(str): quantity(int)}`.
- API: `add(product, qty=1, *, override=False)`, `remove(product)`, `__iter__` (yield {product, quantity, price, subtotal}), `__len__` (к-сть одиниць), `total()`, `clear()`. `save()` → `session.modified = True`.
- Перевірка залишків — у в'юсі/чекауті (не в кошику): не дати додати > stock.

## В'юхи (orders/)
- `cart_detail` (`/cart/`): вміст, форми update/remove, сума.
- `cart_add` (POST `/cart/add/<product_id>/`): + у кошик (qty з форми, cap по stock), redirect.
- `cart_update` / `cart_remove` (POST).
- `CheckoutView` (`/checkout/`, `LoginRequiredMixin`): GET — `OrderForm` (full_name/email/phone/shipping_address + method); POST — валідація (кошик не порожній) → `services.create_order` → clear cart → redirect на сторінку замовлення.
- `OrderListView` (`/orders/`, LoginRequired): лише свої. `OrderDetailView` (`/orders/<pk>/`): лише своє (404).
- Кабінет (`users`) лінкує на `orders:list` через `{% url %}` (без import — без циклу).

## Ядро — `orders/services.py::create_order(user, cart_items, contact) -> Order`
`cart_items`: список `(product, quantity)`. Кроки в `transaction.atomic`:
1. `select_for_update` на товарах; перевірка `qty ≤ stock` інакше `InsufficientStock`.
2. створити `Order`(pending) + `OrderItem` (знімок ціни), порахувати total.
3. зменшити `stock`.
4. `payments.process_payment(order, method)` (мок → `Payment` paid, `order.status=paid`).
5. `transaction.on_commit` → email юзеру + адміну (`send_mail`, console backend у dev).
Повертає `order`. Скасування (`cancelled`) — повертає stock (метод/в'юха, мінімально).

## Форми
`OrderForm(ModelForm[Order])` fields full_name/email/phone/shipping_address + `method`(ChoiceField). Стилі `.Input`.

## Шаблони
`cart.html`, `checkout.html`, `order_detail.html` (підтвердження), `order_list.html` — порт із Hop&Barley (`cart.html`, `checkout.html`, `account.html`), extends base.html. Кнопка «Додати в кошик» на детальній → POST-форма на `orders:cart_add`. Лічильник у navbar (кошик-іконка) — опційно.

## Тести (TDD = критерії)
- Cart: add/override/remove/total/len/clear (сесія).
- cart_add view додає; cart_detail показує суму.
- `create_order`: створює Order(paid)+items+Payment, знімок ціни, зменшує stock, total правильний.
- **Оверселл:** qty>stock → `InsufficientStock`, Order не створено, stock не змінено (atomic rollback).
- checkout: анонім → login; порожній кошик → не створює.
- email надсилається (`mail.outbox`).
- історія: лише свої замовлення; чуже → 404.

## Browser-verify (Playwright)
каталог → товар → «Додати в кошик» → /cart/ → checkout (заповнити форму) → підтвердження замовлення → /orders/ історія. Скріншоти, чистка.

## План (staged)
1. Моделі orders+payments (+міграції, admin, factories) + тести моделей.
2. `Cart` (сесія) + тести.
3. cart-в'юхи + шаблон + add-to-cart на детальній + тести.
4. `services.create_order` + `payments.process_payment` + `InsufficientStock` + email + тести (вкл. оверселл).
5. CheckoutView + OrderForm + шаблон + тести.
6. OrderList/Detail + лінк у кабінеті + тести.
7. Browser-verify повного флоу.
