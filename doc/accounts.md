# App: `accounts`

## Overview

The `accounts` app handles all user-facing authentication features: registration, login, logout, and a simple profile page. It extends Django's built-in `UserCreationForm` to require an email address, but otherwise relies entirely on Django's built-in `User` model — no custom model is needed.

**App namespace**: `accounts`  
**URL prefix** (as registered in `tes/urls.py`): `/accounts/`

---

## Files

```
accounts/
├── __init__.py
├── admin.py      — empty (User is managed via django.contrib.auth)
├── apps.py       — AppConfig (name = "accounts")
├── forms.py      — RegisterForm
├── models.py     — empty (uses Django's built-in User model)
├── urls.py       — URL routing for this app
├── views.py      — register_view, login_view, logout_view, profile
└── templates/
    └── accounts/
        ├── register.html
        ├── login.html
        └── profile.html
```

---

## Models

This app defines **no custom models**. It uses Django's built-in `django.contrib.auth.models.User`.

| Field | Type | Notes |
|-------|------|-------|
| `username` | CharField | Unique, inherited from `AbstractUser` |
| `email` | EmailField | Required via `RegisterForm`.save() |
| `password` | (hashed) | Managed by Django auth |

If you need to extend the user profile (e.g. add a phone number or avatar), the recommended approach is to create a `UserProfile` model with a `OneToOneField(User)` in this app.

---

## Forms

### `RegisterForm` (`forms.py`)

Extends Django's `UserCreationForm`.

```python
class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user
```

**Why override `save()`?** `UserCreationForm` does not save the email by default (it is not in its `Meta.fields`). The override explicitly copies the cleaned email onto the user instance before saving.

**Fields rendered in template:**
- `username` — unique handle
- `email` — required and validated as a valid email address
- `password1` / `password2` — Django's built-in matching password pair

---

## Views

All views are **function-based views (FBVs)**.

### `register_view` (`GET` + `POST`)

| Detail | Value |
|--------|-------|
| URL | `/accounts/register/` |
| Name | `accounts:register` |
| Auth Required | No |
| Template | `accounts/register.html` |

**Flow:**
1. If the user is already authenticated, redirect to `core:home`.
2. `GET`: Render a blank `RegisterForm`.
3. `POST`: Validate the form. If valid, save the user, log them in immediately, display a success message, and redirect to `core:home`. If invalid, re-render the form with errors.

**Context variables passed to template:**

| Variable | Type | Description |
|----------|------|-------------|
| `form` | `RegisterForm` | The bound or unbound registration form |

---

### `login_view` (`GET` + `POST`)

| Detail | Value |
|--------|-------|
| URL | `/accounts/login/` |
| Name | `accounts:login` |
| Auth Required | No |
| Template | `accounts/login.html` |

**Flow:**
1. If already authenticated, redirect to `core:home`.
2. `GET`: Render a bare login page (no Django form object — fields are pulled manually from `request.POST`).
3. `POST`: Call `authenticate(username, password)`. On success, call `login()` and redirect to `core:home`. On failure, add an error message.

> **Design note:** The login view uses raw `request.POST.get()` instead of a Django `AuthenticationForm`. This means field-level validation (e.g., "field is required") must be handled in the template itself. If you reuse this app, consider switching to `AuthenticationForm` for cleaner validation.

---

### `logout_view` (`POST` only)

| Detail | Value |
|--------|-------|
| URL | `/accounts/logout/` |
| Name | `accounts:logout` |
| Auth Required | No (but only accepts POST) |
| Decorator | `@require_POST` |

**Why POST only?** Logging out via a `GET` request is a CSRF vulnerability — a malicious link on another site could silently log users out. `@require_POST` forces the logout to be triggered by a form submission with a CSRF token.

**Logout form pattern in templates:**
```html
<form method="post" action="{% url 'accounts:logout' %}">
  {% csrf_token %}
  <button type="submit">Logout</button>
</form>
```

---

### `profile` (`GET` only)

| Detail | Value |
|--------|-------|
| URL | `/accounts/profile/` |
| Name | `accounts:profile` |
| Auth Required | Yes (`@login_required`) |
| Template | `accounts/profile.html` |

Currently renders a static profile page. The `request.user` object is available in the template via the default context processor (`django.contrib.auth.context_processors.auth`), so you can display `{{ user.username }}`, `{{ user.email }}`, etc. without any extra context.

---

## URL Configuration

```python
# accounts/urls.py
app_name = "accounts"

urlpatterns = [
    path("register/", views.register_view, name="register"),
    path("login/",    views.login_view,    name="login"),
    path("logout/",   views.logout_view,   name="logout"),
    path("profile/",  views.profile,       name="profile"),
]
```

Included in the root URL configuration (`tes/urls.py`) as:
```python
path("accounts/", include("accounts.urls")),
```

---

## Admin

No models are registered in `accounts/admin.py`. The built-in `User` model is managed through `django.contrib.auth`'s default admin registration.

---

## Templates

Templates live in `accounts/templates/accounts/`. Django's template loader finds them because `APP_DIRS = True` in `settings.py`.

| Template | Used By |
|----------|---------|
| `register.html` | `register_view` |
| `login.html` | `login_view` |
| `profile.html` | `profile` |

All templates should extend the project's base layout (typically `base.html` in the root `templates/` folder).

---

## How to Reuse This App in a New Project

1. **Copy the app folder** into your new project directory.
2. Add `"accounts"` to `INSTALLED_APPS`.
3. Include the URLs in your root `urls.py`:
   ```python
   path("accounts/", include("accounts.urls")),
   ```
4. Make sure `LOGIN_URL` and `LOGIN_REDIRECT_URL` are set in settings if you use `@login_required` elsewhere:
   ```python
   LOGIN_URL = "/accounts/login/"
   LOGIN_REDIRECT_URL = "/"
   ```
5. Create the three templates (`register.html`, `login.html`, `profile.html`) that extend your base template.
6. The app has **no migrations** of its own. Run `python manage.py migrate` for the auth app tables.

---

## Known Limitations & Future Improvements

- No password reset / forgot-password flow (Django provides `PasswordResetView` out of the box).
- `login_view` does not use `AuthenticationForm` — validation messages are less granular.
- No email verification step after registration.
- Profile page is read-only — no edit functionality.
