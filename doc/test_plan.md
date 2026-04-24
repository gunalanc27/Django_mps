# Test Plan — `tes` Django E-Commerce Project

**Version**: 1.0  
**Date**: 2026-04-15  
**Scope**: Functional testing of all six Django apps — `accounts`, `cart`, `core`, `products`, `orders`, `reviews`

---

## How to Run Tests

```bash
# Activate virtual environment
source Dvenv/bin/activate

# Run all tests
python manage.py test

# Run tests for a single app
python manage.py test accounts
python manage.py test cart
python manage.py test core
python manage.py test products
python manage.py test orders
python manage.py test reviews

# Run with verbose output
python manage.py test --verbosity=2

# Run tests and keep the test database (useful for debugging)
python manage.py test --keepdb
```

Test files live at `<app>/tests.py`. All test classes should extend `django.test.TestCase`.

---

## 1. `accounts` App

### 1.1 `RegisterForm`

| Test ID | Description | Input | Expected Result |
|---------|-------------|-------|-----------------|
| ACC-F-01 | Valid registration data | All fields filled correctly | Form is valid, `user.email` is saved |
| ACC-F-02 | Missing email | `email=""` | Form invalid; `email` field has error |
| ACC-F-03 | Passwords don't match | `password2 ≠ password1` | Form invalid; `password2` field has error |
| ACC-F-04 | Duplicate username | Existing username | Form invalid; `username` field has error |
| ACC-F-05 | Invalid email format | `email="notanemail"` | Form invalid |
| ACC-F-06 | Password too short | `password1="abc"` | Form invalid (min 8 chars) |
| ACC-F-07 | Numeric-only password | `password1="12345678"` | Form invalid (NumericPasswordValidator) |

### 1.2 `register_view`

| Test ID | Description | Expected Result |
|---------|-------------|-----------------|
| ACC-V-01 | GET `/accounts/register/` as anonymous | 200 OK, form in context |
| ACC-V-02 | GET `/accounts/register/` as authenticated user | Redirect → `core:home` (302) |
| ACC-V-03 | POST valid registration data | User created, user is logged in, redirect → `core:home` |
| ACC-V-04 | POST invalid data | 200 OK, form with errors rendered |

### 1.3 `login_view`

| Test ID | Description | Expected Result |
|---------|-------------|-----------------|
| ACC-V-05 | GET `/accounts/login/` as anonymous | 200 OK |
| ACC-V-06 | GET `/accounts/login/` as authenticated | Redirect → `core:home` |
| ACC-V-07 | POST valid credentials | Logged in, redirect → `core:home`, success message |
| ACC-V-08 | POST wrong password | 200 OK, error message shown |
| ACC-V-09 | POST non-existent username | 200 OK, error message shown |

### 1.4 `logout_view`

| Test ID | Description | Expected Result |
|---------|-------------|-----------------|
| ACC-V-10 | POST `/accounts/logout/` | Logged out, redirect → `core:home`, info message |
| ACC-V-11 | GET `/accounts/logout/` | 405 Method Not Allowed |

### 1.5 `profile`

| Test ID | Description | Expected Result |
|---------|-------------|-----------------|
| ACC-V-12 | GET `/accounts/profile/` as authenticated | 200 OK |
| ACC-V-13 | GET `/accounts/profile/` as anonymous | Redirect → login page (302) |

```python
# Example test skeleton — accounts/tests.py
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from .forms import RegisterForm

class RegisterFormTest(TestCase):
    def test_valid_form(self):
        form = RegisterForm(data={
            "username": "testuser",
            "email": "test@example.com",
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
        })
        self.assertTrue(form.is_valid())

    def test_email_saved_on_commit(self):
        form = RegisterForm(data={
            "username": "testuser",
            "email": "test@example.com",
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
        })
        user = form.save()
        self.assertEqual(user.email, "test@example.com")

class RegisterViewTest(TestCase):
    def test_get_register(self):
        response = self.client.get(reverse("accounts:register"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("form", response.context)

    def test_authenticated_user_redirected(self):
        User.objects.create_user("u", password="pass")
        self.client.login(username="u", password="pass")
        response = self.client.get(reverse("accounts:register"))
        self.assertRedirects(response, reverse("core:home"))

class LogoutViewTest(TestCase):
    def test_get_logout_rejected(self):
        response = self.client.get(reverse("accounts:logout"))
        self.assertEqual(response.status_code, 405)
```

---

## 2. `cart` App

### 2.1 `Cart` Class (Unit Tests)

| Test ID | Description | Expected Result |
|---------|-------------|-----------------|
| CRT-U-01 | `Cart.add()` new product | Item added with correct price and qty=1 |
| CRT-U-02 | `Cart.add()` existing product | Quantity increments, not duplicated |
| CRT-U-03 | `Cart.remove()` | Item removed from session |
| CRT-U-04 | `Cart.update()` valid qty | Quantity updated |
| CRT-U-05 | `Cart.clear()` | Session key reset to `{}` |
| CRT-U-06 | `len(cart)` | Returns sum of all quantities |
| CRT-U-07 | `cart.get_total_price()` | Returns correct Decimal total |
| CRT-U-08 | Iteration (`__iter__`) | Each item has `product`, `price` (Decimal), `total_price` |

### 2.2 Cart Views

| Test ID | Description | Expected Result |
|---------|-------------|-----------------|
| CRT-V-01 | GET `/cart/add/<slug>/` | 405 Method Not Allowed |
| CRT-V-02 | POST `/cart/add/<slug>/` valid slug | Item added, redirect → `cart:cart_detail` |
| CRT-V-03 | POST `/cart/add/<slug>/` invalid slug | 404 Not Found |
| CRT-V-04 | POST `/cart/update/<id>/` with qty > 0 | Quantity updated |
| CRT-V-05 | POST `/cart/update/<id>/` with qty = 0 | Item removed |
| CRT-V-06 | POST `/cart/remove/<slug>/` | Item removed, redirect |
| CRT-V-07 | GET `/cart/` | 200 OK, `cart` in context |
| CRT-V-08 | POST `/cart/clear/` | Cart is empty, redirect |

```python
# Example — cart/tests.py
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from products.models import Category, Product
from .cart import Cart

class CartClassTest(TestCase):
    def setUp(self):
        cat = Category.objects.create(name="Test", slug="test")
        self.product = Product.objects.create(
            name="Widget", slug="widget", category=cat, price="9.99", sku="TST-001"
        )
        self.factory = RequestFactory()

    def _get_cart(self):
        request = self.factory.get("/")
        request.session = self.client.session
        return Cart(request)

    def test_add_and_len(self):
        cart = self._get_cart()
        cart.add(self.product, quantity=3)
        self.assertEqual(len(cart), 3)

    def test_total_price(self):
        cart = self._get_cart()
        cart.add(self.product, quantity=2)
        from decimal import Decimal
        self.assertEqual(cart.get_total_price(), Decimal("19.98"))
```

---

## 3. `core` App

| Test ID | Description | Expected Result |
|---------|-------------|-----------------|
| COR-V-01 | GET `/` | 200 OK; `products` and `categories` in context |
| COR-V-02 | Homepage product count | At most 8 products |
| COR-V-03 | Homepage product ordering | Ordered by `average_rating` descending |
| COR-V-04 | GET `/about/` | 200 OK |
| COR-V-05 | GET `/contact/` | 200 OK |
| COR-V-06 | POST `/contact/` with all fields | Redirect → `/contact/`, success message |
| COR-V-07 | POST `/contact/` missing fields | Should still succeed (no server-side validation on core) |
| COR-V-08 | GET `/partnership/` | 200 OK |
| COR-V-09 | POST `/partnership/` | Redirect → `/partnership/`, success message |

```python
# core/tests.py
from django.test import TestCase
from django.urls import reverse

class CoreViewTests(TestCase):
    def test_home_status(self):
        response = self.client.get(reverse("core:home"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("products", response.context)
        self.assertIn("categories", response.context)

    def test_contact_post(self):
        response = self.client.post(reverse("core:contact"), {
            "name": "Alice", "email": "alice@example.com",
            "subject": "Hello", "message": "Test"
        })
        self.assertRedirects(response, reverse("core:contact"))
```

---

## 4. `products` App

### 4.1 Models

| Test ID | Description | Expected Result |
|---------|-------------|-----------------|
| PRD-M-01 | `Category.save()` auto-generates slug | `category.slug == slugify(category.name)` |
| PRD-M-02 | `Product.save()` auto-generates slug | `product.slug == slugify(product.name)` |
| PRD-M-03 | `Product.save()` auto-generates SKU | `product.sku` is 8-char uppercase hex |
| PRD-M-04 | `Product.is_on_sale` when `original_price > price` | Returns `True` |
| PRD-M-05 | `Product.is_on_sale` when `original_price` is None | Returns `False` |
| PRD-M-06 | `Product.discount_percentage` calculation | Correct rounded percent |
| PRD-M-07 | `Product.is_available` with stock=0 | Returns `False` |
| PRD-M-08 | `Product.is_available` with "Out of Stock" status | Returns `False` |
| PRD-M-09 | `Category` self-referential parent | `child.parent == parent_category` |

### 4.2 Views

| Test ID | Description | Expected Result |
|---------|-------------|-----------------|
| PRD-V-01 | GET `/products/` | 200 OK, up to 12 products per page |
| PRD-V-02 | Filter by category slug | Only products in that category |
| PRD-V-03 | Filter by `?tag=<slug>` | Only tagged products |
| PRD-V-04 | Filter by `?brand=<name>` | Case-insensitive brand filter |
| PRD-V-05 | Search `?q=widget` | Products matching name/brand/description |
| PRD-V-06 | Sort `?sort=price_asc` | Cheapest product first |
| PRD-V-07 | Sort `?sort=price_desc` | Most expensive first |
| PRD-V-08 | Sort `?sort=rating` | Highest rated first |
| PRD-V-09 | GET `/products/product/<slug>/` valid | 200 OK, `product` in context |
| PRD-V-10 | Inactive product detail | 404 Not Found |
| PRD-V-11 | Product detail includes `star_breakdown` | Dict with keys 1–5 |
| PRD-V-12 | Product detail includes `related_products` | Max 4, same category, excluding current |
| PRD-V-13 | GET `/products/categories/` | 200 OK, only top-level categories |

```python
# products/tests.py
from django.test import TestCase
from django.urls import reverse
from .models import Category, Product

class ProductModelTest(TestCase):
    def setUp(self):
        self.cat = Category.objects.create(name="Electronics", slug="electronics")
        self.product = Product.objects.create(
            name="Test Phone", category=self.cat, price="499.99",
            original_price="599.99", stock_quantity=10,
            availability_status="In Stock"
        )

    def test_slug_auto_generated(self):
        self.assertEqual(self.product.slug, "test-phone")

    def test_sku_auto_generated(self):
        self.assertIsNotNone(self.product.sku)
        self.assertEqual(len(self.product.sku), 8)

    def test_is_on_sale(self):
        self.assertTrue(self.product.is_on_sale)

    def test_discount_percentage(self):
        self.assertEqual(self.product.discount_percentage, 17)

    def test_is_available(self):
        self.assertTrue(self.product.is_available)

    def test_product_list_view(self):
        response = self.client.get(reverse("products:product_list"))
        self.assertEqual(response.status_code, 200)
```

---

## 5. `orders` App

### 5.1 Models

| Test ID | Description | Expected Result |
|---------|-------------|-----------------|
| ORD-M-01 | `Order.__str__()` | `"Order #<id> - <username>"` |
| ORD-M-02 | `OrderItem.get_total` | `price * quantity` |
| ORD-M-03 | Default order status | `"pending"` |
| ORD-M-04 | Default `is_paid` | `False` |
| ORD-M-05 | Deleting `Product` with associated `OrderItem` | Raises `ProtectedError` |

### 5.2 Checkout View

| Test ID | Description | Expected Result |
|---------|-------------|-----------------|
| ORD-V-01 | GET `/orders/checkout/` as anonymous | Redirect → login |
| ORD-V-02 | GET `/orders/checkout/` with empty cart | Redirect → `cart:cart_detail`, warning message |
| ORD-V-03 | POST checkout with all valid fields + screenshot | Order created, `is_paid=True`, cart cleared, redirect → confirmation |
| ORD-V-04 | POST checkout missing a required field | 200 re-render with error message listing missing fields |
| ORD-V-05 | POST checkout without screenshot | 200 re-render, "Payment screenshot is required" error |
| ORD-V-06 | Order items count equals cart items | `order.items.count() == len(cart)` |
| ORD-V-07 | Cart is cleared after successful checkout | Session cart is empty |

### 5.3 Order List / Detail

| Test ID | Description | Expected Result |
|---------|-------------|-----------------|
| ORD-V-08 | GET `/orders/list/` as authenticated | 200 OK, only user's own orders |
| ORD-V-09 | GET `/orders/list/` as anonymous | Redirect → login |
| ORD-V-10 | GET `/orders/order/<id>/` as owner | 200 OK |
| ORD-V-11 | GET `/orders/order/<id>/` as different user | 404 Not Found |
| ORD-V-12 | GET `/orders/confirmation/<id>/` | 200 OK |

```python
# orders/tests.py
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from products.models import Category, Product
from .models import Order, OrderItem

class OrderModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("buyer", password="pass")
        cat = Category.objects.create(name="Cat", slug="cat")
        self.product = Product.objects.create(
            name="Item", slug="item", category=cat, price="10.00"
        )
        self.order = Order.objects.create(
            user=self.user, first_name="John", last_name="Doe",
            email="john@example.com", phone="1234567890",
            address="123 Main St", city="Chennai", state="TN",
            postal_code="600001", country="India", total_amount="10.00"
        )

    def test_order_str(self):
        self.assertEqual(str(self.order), f"Order #{self.order.id} - buyer")

    def test_default_status(self):
        self.assertEqual(self.order.status, "pending")

    def test_orderitem_get_total(self):
        item = OrderItem(order=self.order, product=self.product, price="10.00", quantity=3)
        from decimal import Decimal
        self.assertEqual(item.get_total, Decimal("30.00"))

class CheckoutAuthTest(TestCase):
    def test_anonymous_checkout_redirects(self):
        response = self.client.get(reverse("orders:checkout"))
        self.assertNotEqual(response.status_code, 200)
```

---

## 6. `reviews` App

### 6.1 `Review` Model

| Test ID | Description | Expected Result |
|---------|-------------|-----------------|
| REV-M-01 | `Review.save()` updates `product.average_rating` | Product rating recalculated |
| REV-M-02 | `Review.delete()` recalculates rating | Rating drops after deletion |
| REV-M-03 | Only approved reviews count in rating | Unapproved reviews excluded from avg |
| REV-M-04 | `unique_together` prevents duplicate review | `IntegrityError` / `ValidationError` on second review |
| REV-M-05 | `Review.__str__()` | `"<user> — <product> (<rating>★)"` |

### 6.2 `add_review` View

| Test ID | Description | Expected Result |
|---------|-------------|-----------------|
| REV-V-01 | POST as anonymous | Redirect → login |
| REV-V-02 | POST valid rating (1–5) | Review created (`is_approved=False`), success message |
| REV-V-03 | POST invalid rating (0 or 6) | Error message, no review created |
| REV-V-04 | POST second review for same product | Error "You have already reviewed this product" |
| REV-V-05 | POST non-existent product slug | 404 Not Found |

### 6.3 `delete_review` View

| Test ID | Description | Expected Result |
|---------|-------------|-----------------|
| REV-V-06 | Owner deletes own review | Review deleted, redirect → product detail |
| REV-V-07 | Staff deletes any review | Review deleted |
| REV-V-08 | Different user tries to delete | 403 Forbidden |
| REV-V-09 | Non-existent review ID | 404 Not Found |

```python
# reviews/tests.py
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from products.models import Category, Product
from .models import Review

class ReviewModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("reviewer", password="pass")
        cat = Category.objects.create(name="Cat", slug="cat")
        self.product = Product.objects.create(
            name="Gadget", slug="gadget", category=cat, price="50.00"
        )

    def test_review_updates_product_rating(self):
        Review.objects.create(
            product=self.product, user=self.user,
            rating=4, comment="Good", is_approved=True
        )
        self.product.update_rating()
        self.product.refresh_from_db()
        self.assertEqual(float(self.product.average_rating), 4.0)
        self.assertEqual(self.product.review_count, 1)

    def test_unapproved_not_counted(self):
        Review.objects.create(
            product=self.product, user=self.user,
            rating=5, comment="Great"   # is_approved=False by default
        )
        self.product.refresh_from_db()
        self.assertEqual(float(self.product.average_rating), 0.0)

class ReviewViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("u", password="pass")
        cat = Category.objects.create(name="Cat", slug="cat")
        self.product = Product.objects.create(
            name="Gadget", slug="gadget", category=cat, price="50.00"
        )
        self.client.login(username="u", password="pass")

    def test_add_valid_review(self):
        response = self.client.post(
            reverse("reviews:add_review", args=[self.product.slug]),
            {"rating": "5", "title": "Excellent", "comment": "Love it"}
        )
        self.assertEqual(Review.objects.count(), 1)

    def test_invalid_rating_rejected(self):
        self.client.post(
            reverse("reviews:add_review", args=[self.product.slug]),
            {"rating": "0", "comment": "Bad"}
        )
        self.assertEqual(Review.objects.count(), 0)

    def test_duplicate_review_rejected(self):
        Review.objects.create(
            product=self.product, user=self.user, rating=3, comment="OK"
        )
        self.client.post(
            reverse("reviews:add_review", args=[self.product.slug]),
            {"rating": "5", "comment": "Changed mind"}
        )
        self.assertEqual(Review.objects.count(), 1)  # still only one
```

---

## 7. Cross-App Integration Tests

These tests verify that different apps work together correctly.

| Test ID | Description | Expected Result |
|---------|-------------|-----------------|
| INT-01 | Full checkout flow end-to-end | User registers → adds to cart → checks out → order created |
| INT-02 | Product rating updates after review approval | Admin approves review → `average_rating` updated |
| INT-03 | Homepage shows highest-rated products | Products with approved reviews rank first |
| INT-04 | Cart persists across page navigations | Cart data survives GET requests to other pages |
| INT-05 | Cart cleared after successful order | Session cart is empty after checkout |
| INT-06 | Deleting product with no orders succeeds | `Product.delete()` works normally |
| INT-07 | Deleting product with orders raises error | `ProtectedError` raised (admin cannot delete) |

---

## 8. Admin Interface Tests

These are manual tests to be performed via the `/admin/` panel.

| Test ID | Description | Expected Result |
|---------|-------------|-----------------|
| ADM-01 | Approve a review from list view | `is_approved` toggled inline, rating updates |
| ADM-02 | Use "Approve selected reviews" bulk action | All selected reviews approved |
| ADM-03 | Use "Mark selected orders as Shipped" | Status changes to `shipped` |
| ADM-04 | Edit product price inline | Price updated without navigating to detail page |
| ADM-05 | Add new product with all fieldsets | Product saved with auto slug + SKU |
| ADM-06 | View order detail with inline items | Items appear read-only inside Order |
| ADM-07 | Search products by SKU | Correct product returned |
| ADM-08 | Filter orders by status | Only matching orders shown |

---

## 9. Edge Cases & Security Tests

| Test ID | Description | Expected Result |
|---------|-------------|-----------------|
| SEC-01 | CSRF token missing on logout | 403 Forbidden |
| SEC-02 | CSRF token missing on add-to-cart | 403 Forbidden |
| SEC-03 | Access another user's order detail | 404 Not Found |
| SEC-04 | Add item to cart with quantity=0 | Item not added (qty 0 is ignored in `add()`) |
| SEC-05 | SQL injection in `?q=` search param | No error, safe Django ORM |
| SEC-06 | XSS in review comment | Escaped in template (Django auto-escapes) |
| SEC-07 | POST checkout as different user for another's order | Not possible — order is linked to `request.user` |
| SEC-08 | Access `/admin/` as non-staff user | Redirect to admin login |

---

## 10. Test Coverage Targets

| App | Priority | Recommended Coverage |
|-----|----------|----------------------|
| `accounts` | High | ≥ 90% (auth is critical) |
| `cart` | High | ≥ 90% (Cart class is core logic) |
| `orders` | High | ≥ 85% (checkout is the money flow) |
| `reviews` | Medium | ≥ 80% |
| `products` | Medium | ≥ 75% |
| `core` | Low | ≥ 60% (mostly static pages) |

To measure coverage (install `coverage` first):
```bash
pip install coverage
coverage run manage.py test
coverage report
coverage html    # generates htmlcov/index.html for visual report
```
