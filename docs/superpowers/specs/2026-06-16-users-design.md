# Дизайн: апка `users` (автентифікація + кабінет)

> Юніт 3. Спека до загального дизайну (§3.5). Рішення прийняті автономно.
> Цикл: brainstorm → spec → plan → TDD → browser-verify → review → merge.

## Межі юніту
**У межах:** реєстрація, вхід, вихід (session auth), профіль (перегляд+редагування), зміна пароля; підключення нав-лінків (Sign in/Register/account); шаблони з Hop&Barley.
**Поза межами:** історія замовлень (плейсхолдер; оживе в юніті orders), керування адресами (опційне — пропускаємо), скидання пароля поштою (ТЗ вимагає лише *зміну*).

## Рішення
- Базуємось на вбудованих auth-в'юхах Django: `LoginView`, `LogoutView`, `PasswordChangeView`/`PasswordChangeDoneView`. Реєстрація — `RegisterView(CreateView)`.
- Форми: `RegisterForm(UserCreationForm)` з `Meta.model = User`, `fields=("username","email")`; `ProfileForm(ModelForm)` `fields=("first_name","last_name","email")`.
- `RegisterView`: після створення — автологін, редірект у кабінет.
- `ProfileView(LoginRequiredMixin, UpdateView)`: `get_object` → `request.user`.
- URLs (`app_name="users"`, префікс `/account/`): `""`→profile, `register/`, `login/`, `logout/`, `password/`→password_change(+done).
- Settings: `LOGIN_URL="users:login"`, `LOGIN_REDIRECT_URL="users:profile"`, `LOGOUT_REDIRECT_URL="products:list"`.
- Шаблони: `users/templates/users/{login,register,profile,password_change}.html` (extends base.html, порт із login.html/register.html/account.html). Кожна auth-в'юха з явним `template_name`.
- Нав (`base.html`): `Sign in`→`users:login`, `Register`→`users:register`, account-іконка→`users:profile`; кошик лишається `#` (юніт cart). Кнопка «вихід» — у кабінеті.

## Моделі
Без змін (`User` уже є з Юніту 1). Нові поля не потрібні.

## Тести (TDD = критерії)
- register: створює користувача і логінить (редірект, `_auth_user_id` у сесії).
- login: правильні креди → 302/редірект; неправильні → форма з помилкою.
- logout: розлогінює.
- profile: анонім → редірект на login (`LoginRequiredMixin`); залогінений → 200.
- profile edit: POST оновлює first_name/last_name/email.
- password change: змінює пароль (старий не працює, новий працює) — перевірка через `check_password`.

## Browser-verify (Playwright)
register → автологін → кабінет; вихід; вхід; нав показує правильні стани (гість vs залогінений). Скріншоти. Чистка артефактів.
