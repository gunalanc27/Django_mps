# App: `orders`

## Overview

The `orders` app manages the complete checkout and order lifecycle for the e-commerce store. It handles:

1. **Checkout** — collecting shipping details and UPI payment proof from the user
2. **Order creation** — persisting orders and their line items to the database
3. **Google Sheets sync** — pushing order data to a Google Apps Script endpoint in a background thread
4. **Order history** — letting users list and view their past orders

**App namespace**: `orders`  
**URL prefix** (as registered in `tes/urls.py`): `/orders/`

---

## Files

```
orders/
├── __init__.py
├── admin.py    — OrderAdmin (with inline OrderItems and bulk actions)
├── apps.py     — AppConfig (name = "orders")
├── models.py   — Order, OrderItem
├── urls.py     — URL routing
├── views.py    — checkout, order_confirmation, order_list, order_detail
└── templates/
    └── orders/
        ├── checkout.html
        ├── order_confirmation.html
        ├── order_list.html
        └── order_detail.html
```

---

## Models

### `Order`

Represents a single purchase transaction by a user.

| Field | Type | Notes |
|-------|------|-------|
| `user` | ForeignKey(AUTH_USER_MODEL) | CASCADE; `related_name="orders"` |
| `first_name` | CharField(100) | Shipping recipient |
| `last_name` | CharField(100) | — |
| `email` | EmailField | Contact email |
| `phone` | CharField(20) | Contact phone |
| `address` | TextField | Street address |
| `city` | CharField(100) | — |
| `state` | CharField(100) | — |
| `postal_code` | CharField(20) | — |
| `country` | CharField(100) | — |
| `total_amount` | DecimalField(10,2) | Calculated from cart at checkout time |
| `status` | CharField | Choices: `pending`, `confirmed`, `shipped`, `delivered`, `cancelled`; default `pending` |
| `payment_method` | CharField | Choices: `upi_qr`; default `upi_qr` |
| `is_paid` | BooleanField | Default `False`; set to `True` at checkout when screenshot + UTR are submitted |
| `utr_number` | CharField(100) | UPI Transaction Reference Number; `blank=True, null=True` |
| `payment_screenshot` | ImageField | `upload_to="payment_proofs/"`, stored via Cloudinary |
| `created_at` | DateTimeField | Auto |
| `updated_at` | DateTimeField | Auto |

**Ordering**: `["-created_at"]` (newest first)

**`__str__`**: `"Order #<id> - <username>"`

> **Design note on `is_paid`**: At checkout, `is_paid=True` is set as soon as the user submits a screenshot and UTR number. This is an **optimistic payment assumption** — the admin must manually verify the payment and can update `is_paid` if the payment is fraudulent. See admin actions below.

---

### `OrderItem`

A single product line within an order.

| Field | Type | Notes |
|-------|------|-------|
| `order` | ForeignKey(Order) | CASCADE; `related_name="items"` |
| `product` | ForeignKey(Product) | `on_delete=PROTECT` — prevents product deletion if ordered |
| `price` | DecimalField(10,2) | Price at time of order (snapshot) |
| `quantity` | PositiveIntegerField | Default 1 |

**`get_total` property**: Returns `price * quantity`.

**`__str__`**: `"<product name> x <quantity>"`

> **Why `PROTECT` on product?** If `CASCADE` were used, deleting a product would silently delete all order items referencing it, corrupting order history. `PROTECT` raises a `ProtectedError` instead, forcing admins to deactivate products rather than delete them.

---

## Views

All views require **login** (`@login_required`).

### `checkout` (GET + POST)

| Detail | Value |
|--------|-------|
| URL | `/orders/checkout/` |
| Name | `orders:checkout` |
| Auth | Required |
| Template | `orders/checkout.html` |

**GET**: Renders the checkout form with the current cart, UPI ID, and payee name from settings.

**POST flow:**
1. Validates all required fields server-side (first_name, last_name, email, phone, address, city, state, postal_code, country, UTR number).
2. Validates that a `payment_screenshot` file was uploaded.
3. Creates an `Order` with `is_paid=True`.
4. Creates `OrderItem` instances for each cart item.
5. Guards against corrupted cart (if 0 items were saved, deletes the order and redirects).
6. Builds the Google Sheets payload (order details + Cloudinary screenshot URL).
7. Clears the cart from the session.
8. Fires a **daemon thread** to push data to Google Sheets (non-blocking).
9. Redirects to `orders:order_confirmation`.

**Context variables (GET and failed POST):**

| Variable | Description |
|----------|-------------|
| `cart` | Current `Cart` instance |
| `upi_id` | UPI ID from `settings.UPI_ID` |
| `payee_name` | Payee name from `settings.PAYEE_NAME` |

---

### `order_confirmation` (GET)

| Detail | Value |
|--------|-------|
| URL | `/orders/confirmation/<int:order_id>/` |
| Name | `orders:order_confirmation` |
| Auth | Required |
| Template | `orders/order_confirmation.html` |

Uses `get_object_or_404(Order, id=order_id, user=request.user)` — users can only view their own orders.

**Context**: `order`

---

### `order_list` (GET)

| Detail | Value |
|--------|-------|
| URL | `/orders/list/` |
| Name | `orders:order_list` |
| Auth | Required |
| Template | `orders/order_list.html` |

Returns all orders belonging to the current user, ordered by `created_at` descending (via model `Meta`).

**Context**: `orders` (QuerySet)

---

### `order_detail` (GET)

| Detail | Value |
|--------|-------|
| URL | `/orders/order/<int:order_id>/` |
| Name | `orders:order_detail` |
| Auth | Required |
| Template | `orders/order_detail.html` |

Returns a single order. Ownership is enforced with `user=request.user`.

**Context**: `order` (has `order.items.all()` accessible in template)

---

## Google Sheets Sync (`_push_to_sheets`)

```python
def _push_to_sheets(payload):
    url = getattr(settings, 'GOOGLE_SCRIPT_URL', None)
    if not url:
        return
    requests.post(url, json=payload, timeout=10)
```

- Runs in a **daemon thread** (`threading.Thread(..., daemon=True).start()`), so it never blocks the user's request.
- Exceptions are caught silently and logged as warnings — a Sheets sync failure never breaks the checkout.
- Set `GOOGLE_SCRIPT_URL` in your `.env` file to enable syncing. If blank, the function returns immediately.

**Payload fields sent to Google Sheets:**

| Key | Value |
|-----|-------|
| `order_id` | Order PK |
| `username` | User's username |
| `name` | Full name |
| `email` | Email |
| `phone` | Phone |
| `address`, `city`, `state`, `postal_code`, `country` | Shipping info |
| `total_amount` | String decimal |
| `products` | Pipe-separated string: `"Name (SKU, Brand) - Qty: N \| ..."` |
| `screenshot_url` | Cloudinary URL of payment proof |
| `is_paid` | Boolean |
| `utr_number` | UTR string |
| `created_at` | `"YYYY-MM-DD HH:MM:SS"` |

---

## Admin

### `OrderItemInline` (TabularInline)
- Shows order items embedded inside the Order detail page.
- `extra=0` — no blank rows.
- `readonly_fields`: product, price, quantity — prevents modification of historical records.

### `OrderAdmin`
- `list_display`: id, user, first_name, last_name, total_amount, status, created_at
- `list_filter`: status, created_at
- `search_fields`: first_name, last_name, email, id
- `list_per_page`: 25
- `inlines`: OrderItemInline

**Bulk Actions:**

| Action | Effect |
|--------|--------|
| `mark_confirmed` | Sets `status="confirmed"` on all selected orders |
| `mark_shipped` | Sets `status="shipped"` |
| `mark_delivered` | Sets `status="delivered"` |
| `mark_cancelled` | Sets `status="cancelled"` |

---

## Required Settings

```python
UPI_ID          = os.environ.get("UPI_ID", "gpzstore@oksbi")
PAYEE_NAME      = os.environ.get("PAYEE_NAME", "GPZ Store")
GOOGLE_SCRIPT_URL = os.environ.get("GOOGLE_SCRIPT_URL", "")
```

`payment_screenshot` is uploaded to Cloudinary (via `STORAGES["default"]`). Ensure Cloudinary is configured in `.env` before running checkout in production.

---

## URL Configuration

```python
# orders/urls.py
app_name = "orders"

urlpatterns = [
    path("checkout/",                      views.checkout,           name="checkout"),
    path("confirmation/<int:order_id>/",   views.order_confirmation, name="order_confirmation"),
    path("list/",                          views.order_list,         name="order_list"),
    path("order/<int:order_id>/",          views.order_detail,       name="order_detail"),
]
```

---

## Dependencies

| Dependency | Why |
|------------|-----|
| `cart.cart.Cart` | Reads cart data; clears it after successful order |
| `products.models.Product` | Referenced by `OrderItem.product` |
| `requests` | HTTP POST to Google Sheets |
| `threading` | Non-blocking Google Sheets sync |
| Cloudinary | Payment screenshot storage |

---

## How to Reuse This App in a New Project

1. **Copy the `orders/` folder**.
2. Add `"orders"` to `INSTALLED_APPS`.
3. Include URLs:
   ```python
   path("orders/", include("orders.urls")),
   ```
4. Run migrations:
   ```bash
   python manage.py makemigrations orders
   python manage.py migrate
   ```
5. Add required settings (`UPI_ID`, `PAYEE_NAME`, `GOOGLE_SCRIPT_URL`) to `.env`.
6. To disable Google Sheets sync, set `GOOGLE_SCRIPT_URL=""` — the function exits early.
7. Ensure `cart` app is also installed (the checkout view reads from `Cart`).
8. Configure Cloudinary (or swap `payment_screenshot` to a regular `FileField` if not using cloud storage).

---

## Known Limitations & Future Improvements

- **No inventory decrement**: `stock_quantity` on `Product` is not reduced when an order is placed.
- **`is_paid=True` is optimistic**: A user could upload a fake screenshot. Admin review is required.
- **No order cancellation view** for users (only admins can cancel via admin actions).
- **No webhook / payment gateway**: Relies entirely on manual UPI + screenshot verification.
- Google Sheets sync uses a daemon thread — if the process crashes immediately after `cart.clear()`, the sync may be lost.
