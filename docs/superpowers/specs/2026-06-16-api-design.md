# Дизайн: REST API (DRF + JWT + OpenAPI)

> Юніт 6. Загальний дизайн §3.7, §3.8. Рішення автономні. Спека з планом.

## Межі
**У межах:** central `api/` app — серіалізатори, viewsets, permissions, роутер; JWT (simplejwt); OpenAPI (drf-spectacular) на `/api/docs/`. Ендпоінти: products (RO, фільтри/пошук/сорт/пагінація), reviews (`/api/products/<id>/reviews/`), orders (CRUD, лише свої, create з БД-кошика), cart (`/api/cart/` — модель `orders.CartItem`), users (register, login-JWT, refresh).
**Поза межами:** GraphQL (бонус-юніт), вебхуки оплати.

## Залежності/конфіг
- `rest_framework`, `django_filters`, `drf_spectacular` у INSTALLED_APPS.
- DRF: `DEFAULT_AUTHENTICATION_CLASSES=[JWTAuthentication, SessionAuthentication]`, `DEFAULT_PERMISSION_CLASSES=[IsAuthenticatedOrReadOnly]`, `PageNumberPagination` (page_size 12), `DEFAULT_SCHEMA_CLASS=drf_spectacular`. `SPECTACULAR_SETTINGS` (title). mypy: `ignore_missing_imports` для DRF-модулів.

## Нова модель `orders.CartItem` (БД-кошик для API)
`user`(FK AUTH_USER_MODEL), `product`(FK Product, PROTECT), `quantity`(PositiveInt), `unique_together(user, product)`, `created_at`. (Веб лишається на сесії; API — стейтлес → БД.)

## api/ app
- **serializers:** Category, Product (з avg_rating read-only), Review, OrderItem, Order (nested items, read-only user/status/total), CartItem (product_id write, product nested read), Register (username/email/password, валідація).
- **viewsets/views:**
  - `ProductViewSet(ReadOnlyModelViewSet)` — `active().select_related(category)`, DjangoFilterBackend (category, ціна) + SearchFilter (name, description) + OrderingFilter (price, created_at). AllowAny.
  - `ReviewListCreateAPIView` (`/api/products/<pk>/reviews/`): GET список; POST — `IsAuthenticated`, перевірка `can_review` (reuse reviews.services), product з URL, user з request.
  - `OrderViewSet(ModelViewSet)` — `IsAuthenticated`+`IsOwner`; `get_queryset` лише свої; `create` → з `CartItem` юзера через `orders.services.create_order` + `payments.process_payment`, очистити CartItem. `perform_*` заборонити чуже.
  - `CartItemViewSet(ModelViewSet)` — `IsAuthenticated`; лише свої CartItem; create/update (qty, cap stock).
  - users: `RegisterAPIView(CreateAPIView)`; login=`TokenObtainPairView`; refresh=`TokenRefreshView`.
- **permissions:** `IsOwner` (obj.user == request.user).
- **urls** (`/api/`): router (products, cart, orders) + `products/<pk>/reviews/` + `users/register|login|refresh` + `schema`/`docs` (spectacular).

## Тести (TDD = критерії)
- products: GET список (200, пагінація), фільтр/пошук; запис заборонено анону (RO).
- JWT: register → login повертає access/refresh; protected без токена → 401.
- cart: додати/переглянути лише свої.
- order create: з кошика → 201, статус paid, stock списано, кошик очищено; чужі замовлення не видно (IsOwner).
- reviews API: не-покупець POST → 403/400; покупець → 201.
- `/api/schema/` та `/api/docs/` → 200.

## План (staged)
1. settings + CartItem(+міграція,admin) + mypy-оверайди.
2. serializers.
3. permissions + products/cart/reviews viewsets + urls + spectacular.
4. orders viewset (create з кошика) + users register/JWT.
5. Тести + verify (вкл. /api/docs/). Browser-verify Swagger.
