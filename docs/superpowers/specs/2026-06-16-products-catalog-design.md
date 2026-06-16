# Дизайн: апка `products` (каталог)

> Юніт 2. Спека до загального дизайну `2026-06-16-django-shop-design.md` (§3.1, §4).
> Затверджено 2026-06-16. HTML-основа: Hop-and-Barley (`home.html` + product-сторінки).
> Цикл: brainstorm(✓) → spec(цей файл) → plan → TDD → completion.

## 1. Межі юніту

**У межах:** моделі `Category`/`Product`, admin, factories, seed-команда, каталог-лист (фільтри/пошук/сорт/пагінація), детальна сторінка (інфо), `base.html` зі спільного хедера/футера шаблону, статика.

**Поза межами (наступні юніти):** відгуки (reviews), «додати в кошик» (orders/cart), сорт за популярністю (після появи `OrderItem`), вкладені категорії у фільтрі, full-text пошук.

## 2. Моделі

### Category
- `name: CharField`
- `slug: SlugField(unique=True)` — авто зі `slugify(name)`, якщо порожній
- `parent: ForeignKey("self", null=True, blank=True, on_delete=SET_NULL, related_name="children")`
- `created_at/updated_at: DateTimeField(auto_now_add / auto_now)`
- `Meta.ordering = ["name"]`, `verbose_name_plural = "categories"`; `__str__ -> name`

### Product
- `name: CharField`
- `slug: SlugField(unique=True)` — авто зі `slugify(name)`, якщо порожній
- `description: TextField`
- `price: DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])`
- `category: ForeignKey(Category, on_delete=PROTECT, related_name="products")` — `PROTECT`: не дати видалити категорію з товарами
- `image: ImageField(upload_to="products/", blank=True)` — опційне; фолбек на статичний плейсхолдер у шаблоні
- `is_active: BooleanField(default=True)`
- `stock: PositiveIntegerField(default=0)`
- `created_at/updated_at`
- Менеджер/QuerySet: `Product.objects.active()` → `filter(is_active=True)`
- `Meta.ordering = ["-created_at"]`; `__str__ -> name`; `get_absolute_url()` → детальна

Slug-логіка — в `save()`: якщо `slug` порожній, `slug = slugify(name)`. На колізії покладаємось на `unique=True` (sample-дані унікальні).

## 3. Каталог — `ProductListView` (`/` та `/products/`)

- База: `Product.objects.active().select_related("category")` (анти-N+1).
- **Фільтри (GET):** `category` (slug), `min_price`, `max_price`.
- **Пошук:** `q` → `Q(name__icontains=q) | Q(description__icontains=q)`.
- **Сорт:** `sort ∈ {price, -price, -created_at}` (whitelist; дефолт `-created_at`). Невалідні значення ігноруються.
- **Пагінація:** `paginate_by = 12`.
- Уся логіка — у `get_queryset()` вручну (без `django-filter`; його застосуємо для API). У контекст: список категорій для бічного фільтра, поточні значення фільтрів/сорту (щоб форма й пагінація їх зберігали).

## 4. Детальна — `ProductDetailView` (`/product/<slug>/`)

- `Product.objects.active().select_related("category")`, lookup за `slug`; 404 для inactive/відсутнього.
- Контекст: товар (назва, опис, ціна, зображення, характеристики, категорія).
- **Плейсхолдери** (явно позначені коментарем у шаблоні): блок відгуків → юніт reviews; кнопка «в кошик» → юніт orders/cart. Поки неактивні/статичні.

## 5. Шаблони і статика

- `base.html` — витягнути спільний хедер/нав/футер із шаблону Hop-and-Barley + підключення `main.css`, шрифтів, потрібного JS. Замінює мінімальний `base.html` з Юніту 1.
- `products/templates/products/product_list.html` — порт `home.html`: грід-картки через `{% for product in products %}`, GET-форма фільтрів/сорту, контроли пагінації. Клієнтський JS-фільтр прибрати (сорт/фільтр серверні).
- `products/templates/products/product_detail.html` — порт product-сторінки, динамічні поля + плейсхолдери.
- Статика: скопіювати `main.css`, `img/`, потрібний `js/` у `static/`. Зображення товару → фолбек на статичний плейсхолдер, якщо `image` порожнє.
- Нав-лінки на ще-не-існуючі сторінки (cart/account/login) — тимчасові `href="#"`, замінимо на `{% url %}` у відповідних юнітах (щоб шаблон не падав).

## 6. Admin

- `CategoryAdmin`: `list_display=(name, slug, parent)`, `search_fields=(name,)`, `prepopulated_fields={"slug": ("name",)}`.
- `ProductAdmin`: `list_display=(name, category, price, stock, is_active)`, `list_filter=(category, is_active)`, `search_fields=(name, description)`, `prepopulated_fields={"slug": ("name",)}`, `list_editable=(price, stock, is_active)`.
- Аналітика/агрегації — окремий юніт (тиждень 3).

## 7. Seed + factories

- `factory_boy`: `CategoryFactory`, `ProductFactory` (`products/tests/factories.py`).
- Management-команда `seed_catalog` (`products/management/commands/`): створює 4 категорії (Hops, Malts, Yeast, Kits) + 12 товарів зі статичного шаблону (назви/описи/ціни/stock). Ідемпотентна (`get_or_create`), без зображень. Для dev/демо, не для тестів.

## 8. URLs

- `products/urls.py` (app_name="products"): `""`/`products/` → list (name="list"), `product/<slug:slug>/` → detail (name="detail").
- Підключити в `config/urls.py`: `path("", include("products.urls"))`.

## 9. Тести (TDD — пишемо першими; це й є критерії готовності)

**Моделі** (`test_models.py`):
- авто-генерація slug зі `name`; `__str__`; `MinValueValidator` на ціні (full_clean); `Product.objects.active()` віддає лише `is_active=True`; `unique` slug.

**Каталог** (`test_views.py`):
- віддає лише active; пагінація (12); фільтр за категорією; фільтр ціни (min/max); пошук за name; пошук за description; сорт price/-price/newest; немає N+1 (`assertNumQueries` зі `select_related`).

**Детальна** (`test_views.py`):
- 200 за slug активного товару; 404 для inactive і неіснуючого; контекст містить товар.

**Seed** (`test_seed.py`): команда створює очікувані категорії/товари; повторний запуск не дублює.

Все зелене + `ruff`/`mypy` чисті; нові тести покривають моделі та в'юхи.

## 10. План реалізації (staged, TDD)

1. Моделі + міграції + менеджер + admin + factories (+ тести моделей).
2. `seed_catalog` (+ тест).
3. Каталог-лист: view + url + шаблон + статика + `base.html` (+ тести каталогу).
4. Детальна: view + url + шаблон (+ тести детальної).
