# App: `cart`

## Overview

The `cart` app implements a **session-based shopping cart**. No database table is created — cart data is stored entirely in the Django session as a Python dictionary. The `Cart` class is the core abstraction; it wraps the session and provides a clean API for adding, updating, removing, and iterating cart items.

A **context processor** (`cart_context`) injects the `Cart` object into every template automatically, so the cart item count and totals are always available in the navigation bar without any extra view code.

**App namespace**: `cart`  
**URL prefix** (as registered in `tes/urls.py`): `/cart/`

---

## Files

```
cart/
├── __init__.py
├── admin.py      — empty (no DB models)
├── apps.py       — AppConfig (name = "cart")
├── cart.py       — Cart class + cart_context context processor
├── models.py     — empty (session-only, no models)
├── urls.py       — URL routing
├── views.py      — add_to_cart, update_cart, remove_from_cart, cart_detail, clear_cart
└── templates/
    └── cart/
        └── cart_detail.html
```

---

## Session Storage

Cart data is keyed in the Django session using the `CART_SESSION_ID` setting (defined as `"cart"` in `settings.py`).

**Data structure stored in the session:**
```python
{
    "<product_id_str>": {
        "quantity": <int>,
        "price": "<str decimal>",   # stored as string to avoid JSON serialization issues
    },
    ...
}
```

Product IDs are stored as **strings** because Django's session backend serializes to JSON, and JSON object keys must be strings.

---

## The `Cart` Class (`cart/cart.py`)

### Initialization

```python
class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart
```

Retrieves the cart dict from the session. If no cart exists yet, creates an empty dict and stores it.

### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `add` | `add(product, quantity=1)` | Adds a product to the cart. If the product is already in the cart, increments quantity. |
| `update` | `update(product_id, quantity)` | Sets the quantity for an existing cart item directly. |
| `remove` | `remove(product_id)` | Removes an item from the cart dict. |
| `clear` | `clear()` | Replaces the cart with an empty dict, effectively emptying it. |
| `save` | `save()` | Marks the session as modified so Django persists it. Must be called after every mutation. |
| `get_total_price` | `get_total_price()` | Returns total cost as a `Decimal`. |
| `__len__` | — | Returns total number of items (sum of all quantities). Used in templates as `{{ cart|length }}`. |
| `__iter__` | — | Iterates over cart items. Fetches Product objects from DB in one query, enriches items with `product`, `price` (as `Decimal`), and `total_price`. |

### Iteration Example

```python
for item in cart:
    item["product"]     # Product model instance
    item["price"]       # Decimal
    item["quantity"]    # int
    item["total_price"] # Decimal (price × quantity)
```

The `__iter__` method does a single `Product.objects.filter(id__in=product_ids)` query — **not** N+1.

---

## Context Processor

```python
def cart_context(request):
    return {"cart": Cart(request)}
```

Registered in `settings.py`:
```python
"context_processors": [
    ...
    "cart.cart.cart_context",
],
```

This makes `{{ cart }}` available in **every** template. Common usages:

```html
{{ cart|length }}          {# total item count for nav badge #}
{{ cart.get_total_price }} {# total cost #}
{% for item in cart %}     {# iterate cart items #}
```

---

## Views

All cart views require **POST** (using `@require_POST`) to prevent browsers, bots, or prefetch crawlers from accidentally modifying the cart via `GET` requests.

### `add_to_cart` (POST)

| Detail | Value |
|--------|-------|
| URL | `/cart/add/<slug:slug>/` |
| Name | `cart:add_to_cart` |
| Auth | Not required |

Looks up the product by slug, reads `quantity` from POST body (defaults to 1), calls `cart.add()`, redirects to cart detail.

**Typical HTML form:**
```html
<form method="post" action="{% url 'cart:add_to_cart' product.slug %}">
  {% csrf_token %}
  <input type="hidden" name="quantity" value="1">
  <button type="submit">Add to Cart</button>
</form>
```

---

### `update_cart` (POST)

| Detail | Value |
|--------|-------|
| URL | `/cart/update/<int:product_id>/` |
| Name | `cart:update_cart` |
| Auth | Not required |

Reads new `quantity` from POST. If `quantity > 0`, updates. If `quantity <= 0`, removes the item (treats 0 as "delete").

---

### `remove_from_cart` (POST)

| Detail | Value |
|--------|-------|
| URL | `/cart/remove/<slug:slug>/` |
| Name | `cart:remove_from_cart` |
| Auth | Not required |

Looks up the product by slug, removes it from the cart by its numeric ID.

---

### `cart_detail` (GET)

| Detail | Value |
|--------|-------|
| URL | `/cart/` |
| Name | `cart:cart_detail` |
| Auth | Not required |
| Template | `cart/cart_detail.html` |

Renders the cart page. The `cart` object is already in context via the context processor, but is also passed explicitly for clarity.

**Context variables:**

| Variable | Type | Description |
|----------|------|-------------|
| `cart` | `Cart` | The current cart |

---

### `clear_cart` (POST)

| Detail | Value |
|--------|-------|
| URL | `/cart/clear/` |
| Name | `cart:clear_cart` |
| Auth | Not required |

Calls `cart.clear()` and redirects back to `cart:cart_detail`.

---

## URL Configuration

```python
# cart/urls.py
app_name = "cart"

urlpatterns = [
    path("",                          views.cart_detail,       name="cart_detail"),
    path("add/<slug:slug>/",          views.add_to_cart,       name="add_to_cart"),
    path("update/<int:product_id>/",  views.update_cart,       name="update_cart"),
    path("remove/<slug:slug>/",       views.remove_from_cart,  name="remove_from_cart"),
    path("clear/",                    views.clear_cart,         name="clear_cart"),
]
```

---

## Required Settings

```python
# settings.py
CART_SESSION_ID = "cart"   # The session key used to store cart data
```

Also ensure `django.contrib.sessions` is in `INSTALLED_APPS` and the session middleware is active.

---

## Dependencies

| Dependency | Why |
|------------|-----|
| `products.models.Product` | Cart items are resolved to Product instances on iteration |
| `django.contrib.sessions` | Cart is entirely session-based |

---

## How to Reuse This App in a New Project

1. **Copy the `cart/` folder** into your project.
2. Add `"cart"` to `INSTALLED_APPS`.
3. Add `CART_SESSION_ID = "cart"` to your `settings.py`.
4. Register the context processor in `settings.py`:
   ```python
   "cart.cart.cart_context",
   ```
5. Include the URLs:
   ```python
   path("cart/", include("cart.urls")),
   ```
6. Ensure `django.contrib.sessions` is enabled and migrated.
7. **Adapt the import**: The `Cart` class imports `from products.models import Product`. Change this to match your product model location.
8. Create the `cart/templates/cart/cart_detail.html` template.

---

## Known Limitations & Future Improvements

- **No stock validation**: Adding more items than available stock is allowed silently.
- **No authentication guard**: Anonymous users can add items. If your checkout requires login, the cart will persist across login via the session.
- **Price stored at add-time**: If a product's price changes, the cart shows the old price until the session expires or the item is re-added. This is intentional for price consistency during checkout.
- **No coupon / discount support** built in.
