# App: `core`

## Overview

The `core` app is the **landing hub** of the project. It renders public-facing pages that don't belong to any specific domain model (products, orders, etc.). It serves as the entry point for visitors and handles the homepage, about page, contact form, and a partnership inquiry form.

**App namespace**: `core`  
**URL prefix** (as registered in `tes/urls.py`): `/` (root)

---

## Files

```
core/
├── __init__.py
├── admin.py      — minimal (only site title registration)
├── apps.py       — AppConfig (name = "core")
├── models.py     — empty
├── urls.py       — URL routing
├── views.py      — home, about, contact, partnership
└── templates/
    └── core/
        ├── home.html
        ├── about.html
        ├── contact.html
        └── partnership.html
```

---

## Models

This app defines **no models**. All displayed data is pulled from other apps (`products.Product`, `products.Category`).

---

## Views

All views are **function-based views (FBVs)**.

### `home` (GET)

| Detail | Value |
|--------|-------|
| URL | `/` |
| Name | `core:home` |
| Auth | Not required |
| Template | `core/home.html` |

Queries the database for:
- **8 active products**, ordered by highest average rating (`-average_rating`)
- **6 active categories** (top-level)

**Context variables:**

| Variable | Type | Description |
|----------|------|-------------|
| `products` | QuerySet | 8 top-rated active products |
| `categories` | QuerySet | Up to 6 active categories |

**Query details:**
```python
products   = Product.objects.filter(is_active=True).order_by("-average_rating")[:8]
categories = Category.objects.filter(is_active=True)[:6]
```

> No filtering by `parent=None` is done for categories on the homepage — any category (including subcategories) can appear. If you want only top-level categories, add `.filter(parent=None)`.

---

### `about` (GET)

| Detail | Value |
|--------|-------|
| URL | `/about/` |
| Name | `core:about` |
| Auth | Not required |
| Template | `core/about.html` |

Static page, no context variables. Renders company/project information.

---

### `contact` (GET + POST)

| Detail | Value |
|--------|-------|
| URL | `/contact/` |
| Name | `core:contact` |
| Auth | Not required |
| Template | `core/contact.html` |

**Flow:**
1. `GET`: Render the contact form.
2. `POST`: Read `name`, `email`, `subject`, `message` from POST data. Log the submission via Python's `logging` module. Display a success flash message and redirect to `core:contact` (PRG pattern — prevents resubmission on page refresh).

> **Important**: The contact form does **not** send an actual email. It only logs to the Django logger. To enable real email sending, add `send_mail()` from `django.core.mail` in the POST handler. The comment `# In a real app, send_mail() would be called here` marks the correct location.

**Logged fields:** `name`, `email`, `subject` (message is not logged to avoid logging PII).

---

### `partnership` (GET + POST)

| Detail | Value |
|--------|-------|
| URL | `/partnership/` |
| Name | `core:partnership` |
| Auth | Not required |
| Template | `core/partnership.html` |

A business partnership inquiry form. Works identically to `contact` — reads `business_name` and `contact_person`, logs the inquiry, shows a success message, and redirects. No email is sent.

---

## URL Configuration

```python
# core/urls.py
app_name = "core"

urlpatterns = [
    path("",              views.home,        name="home"),
    path("about/",        views.about,       name="about"),
    path("contact/",      views.contact,     name="contact"),
    path("partnership/",  views.partnership, name="partnership"),
]
```

---

## Logging

Both `contact` and `partnership` use Python's `logging` module:

```python
import logging
logger = logging.getLogger(__name__)
```

The logger name will be `core.views`. Configure a handler in `settings.py` if you want these logs to appear in a file or external service:
```python
LOGGING = {
    "version": 1,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "loggers": {"core": {"handlers": ["console"], "level": "INFO"}},
}
```

---

## How to Reuse This App in a New Project

1. **Copy the `core/` folder** into your project.
2. Add `"core"` to `INSTALLED_APPS`.
3. Include the URLs at the root:
   ```python
   path("", include("core.urls")),
   ```
4. The home view **depends on `products.models`**. Either:
   - Keep the `products` app and this import, or
   - Remove the product/category queries and pass empty lists if your project has no products.
5. Create the four templates (`home.html`, `about.html`, `contact.html`, `partnership.html`).
6. To add real email sending, install `django.core.mail` and add an SMTP backend in settings:
   ```python
   EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
   EMAIL_HOST = "smtp.gmail.com"
   # ... etc.
   ```

---

## Known Limitations & Future Improvements

- Contact and partnership forms save **no data** to the database — submissions are lost on log rotation.
- No spam protection (no CAPTCHA, rate limiting, or honeypot).
- No email notifications to admins.
- Homepage product ordering by `average_rating` means new products with 0 reviews appear last — consider a "featured" flag on the `Product` model.
