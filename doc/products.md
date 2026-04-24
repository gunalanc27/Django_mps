# App: `products`

## Overview

The `products` app is the **central catalogue** of the e-commerce project. It defines three models — `Category`, `Tag`, and `Product` — and provides class-based views for browsing products with filtering, sorting, and searching. It also hosts review-aggregate fields (`average_rating`, `review_count`) that are updated by the `reviews` app whenever a review is saved or deleted.

**App namespace**: `products`  
**URL prefix** (as registered in `tes/urls.py`): `/products/`

---

## Files

```
products/
├── __init__.py
├── admin.py        — CategoryAdmin, TagAdmin, ProductAdmin (rich fieldsets)
├── apps.py         — AppConfig (name = "products")
├── management/     — Custom management commands (if any)
├── models.py       — Category, Tag, Product
├── urls.py         — URL routing
├── views.py        — ProductListView, ProductDetailView, CategoryListView
└── templates/
    └── products/
        ├── product_list.html
        ├── product_detail.html
        └── category_list.html
```

---

## Models

### `Category`

Hierarchical product grouping (e.g. *Electronics → Mobiles*).

| Field | Type | Notes |
|-------|------|-------|
| `name` | CharField(100) | Unique |
| `slug` | SlugField(120) | Unique; auto-generated from `name` if blank |
| `description` | TextField | Optional |
| `parent` | ForeignKey("self") | `null=True`; enables tree structure. `related_name="children"` |
| `image_url` | URLField(500) | External image link for category card/banner |
| `display_order` | IntegerField | Controls ordering in lists (lower = first) |
| `is_active` | BooleanField | Soft enable/disable |
| `created_at` | DateTimeField | Auto-set on creation |
| `updated_at` | DateTimeField | Auto-updated |

**Ordering**: `["display_order", "name"]`

**`save()` override**: Auto-generates `slug = slugify(name)` if `slug` is blank.

**`get_absolute_url()`**: Returns `products:category_detail` URL.

**Self-referential FK pattern:**
```python
parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="children")
```
Top-level categories have `parent=None`. To get all children of a category:
```python
category.children.filter(is_active=True)
```

---

### `Tag`

Short keyword labels attached to products (e.g. *5G*, *OLED*, *Gaming*).

| Field | Type | Notes |
|-------|------|-------|
| `name` | CharField(50) | Unique |
| `slug` | SlugField(60) | Unique; auto-generated |
| `description` | CharField(200) | Optional summary |
| `is_active` | BooleanField | — |
| `created_at` / `updated_at` | DateTimeField | Auto timestamps |

**Ordering**: `["name"]`

---

### `Product`

The main product entity. Rich model supporting SKU, brand, pricing with discount, JSON specs, image gallery, and review aggregation.

#### Fields

**Identity**

| Field | Type | Notes |
|-------|------|-------|
| `sku` | CharField(50) | Unique; auto-generated as 8-char UUID fragment if blank |
| `name` | CharField(255) | Product display name |
| `slug` | SlugField(255) | Unique; auto-generated from `name` |
| `brand` | CharField(100) | Optional |
| `model_number` | CharField(100) | Optional |

**Description**

| Field | Type | Notes |
|-------|------|-------|
| `short_description` | CharField(500) | For list cards |
| `long_description` | TextField | Full detail page description |

**Pricing**

| Field | Type | Notes |
|-------|------|-------|
| `price` | DecimalField(10,2) | Current selling price |
| `original_price` | DecimalField(10,2) | `null=True`; original/MRP before discount |
| `currency` | CharField(3) | Default `"INR"` |

**Stock & Availability**

| Field | Type | Notes |
|-------|------|-------|
| `stock_quantity` | PositiveIntegerField | Default 0 |
| `availability_status` | CharField | Choices: `In Stock`, `Out of Stock`, `Pre-Order`, `Discontinued` |

**Relations**

| Field | Type | Notes |
|-------|------|-------|
| `category` | ForeignKey(Category) | `on_delete=CASCADE`; `related_name="products"` |
| `tags` | ManyToManyField(Tag) | Optional; `related_name="products"` |

**Media**

| Field | Type | Notes |
|-------|------|-------|
| `image` | ImageField | Legacy single image; stored via Cloudinary |
| `image_gallery` | JSONField | List of image URLs for a gallery carousel |
| `video_url` | URLField(500) | Optional promo video |

**Specifications**

| Field | Type | Notes |
|-------|------|-------|
| `specifications` | JSONField | Arbitrary key-value dict: `{"RAM": "8GB", "Display": "6.1"}` |

**Review Aggregates** *(read-only; updated by `reviews` app)*

| Field | Type | Notes |
|-------|------|-------|
| `average_rating` | DecimalField(3,2) | Default `0.00` |
| `review_count` | IntegerField | Default 0 |

**Timestamps**

| Field | Type | Notes |
|-------|------|-------|
| `is_active` | BooleanField | Soft delete / hide |
| `created_at` | DateTimeField | Auto |
| `updated_at` | DateTimeField | Auto |

**Ordering**: `["-created_at"]`

#### Properties

| Property | Returns | Description |
|----------|---------|-------------|
| `is_on_sale` | bool | True if `original_price` exists and is greater than `price` |
| `discount_percentage` | int | Rounded percentage off original price |
| `is_available` | bool | True if `availability_status == "In Stock"` AND `stock_quantity > 0` |

#### Methods

| Method | Description |
|--------|-------------|
| `get_absolute_url()` | Returns `products:product_detail` URL |
| `get_add_to_cart_url()` | Returns `cart:add_to_cart` URL |
| `get_remove_from_cart_url()` | Returns `cart:remove_from_cart` URL |
| `update_rating()` | Recalculates `average_rating` and `review_count` from approved reviews. Called by `reviews.models.Review.save()` and `Review.delete()`. |

**`save()` override:**
```python
def save(self, *args, **kwargs):
    if not self.slug:
        self.slug = slugify(self.name)
    if not self.sku:
        self.sku = str(uuid.uuid4())[:8].upper()
    super().save(*args, **kwargs)
```

**`update_rating()` — lazy import pattern:**
```python
def update_rating(self):
    from reviews.models import Review   # ← lazy import avoids circular dependency
    approved = Review.objects.filter(product=self, is_approved=True)
    ...
```

---

## Views

All views are **class-based views (CBVs)**.

### `ProductListView` (GET)

| Detail | Value |
|--------|-------|
| URL | `/products/` or `/products/category/<category_slug>/` |
| Names | `products:product_list`, `products:category_detail` |
| Auth | Not required |
| Template | `products/product_list.html` |
| Paginate By | 12 |

**Filtering (via GET query parameters):**

| Parameter | Filter Applied |
|-----------|---------------|
| `category_slug` (URL kwarg) | `category__slug=category_slug` |
| `?tag=<slug>` | `tags__slug=tag_slug` |
| `?brand=<name>` | `brand__iexact=brand` |
| `?q=<text>` | Full-text search across `name`, `brand`, `short_description`, `long_description`, `model_number` |

**Sorting (via `?sort=` parameter):**

| Value | Order |
|-------|-------|
| `price_asc` | Cheapest first |
| `price_desc` | Most expensive first |
| `rating` | Highest rated first |
| `newest` (default) | Most recently added |

**Context variables injected:**

| Variable | Description |
|----------|-------------|
| `products` | Paginated product queryset |
| `categories` | Top-level active categories (for sidebar/nav) |
| `all_tags` | All active tags |
| `brands` | Distinct brand values of active products |
| `current_category` | Category object if filtering by category |
| `current_tag` | Current tag slug string |
| `current_brand` | Current brand string |
| `current_sort` | Current sort key |
| `search_query` | Current search string |

---

### `ProductDetailView` (GET)

| Detail | Value |
|--------|-------|
| URL | `/products/product/<slug:slug>/` |
| Name | `products:product_detail` |
| Auth | Not required |
| Template | `products/product_detail.html` |
| Slug field | `slug` |

**Context variables injected:**

| Variable | Description |
|----------|-------------|
| `product` | The `Product` instance |
| `reviews` | QuerySet of approved reviews |
| `review_count` | Integer count of approved reviews |
| `star_breakdown` | Dict `{5: {count, percentage}, 4: ..., ...}` for rating bar chart |
| `user_review` | Current user's own review (if authenticated), or `None` |
| `related_products` | Up to 4 active products in the same category, ordered by rating |
| `spec_items` | `list(product.specifications.items())` — ready for `{% for key, value in spec_items %}` |

---

### `CategoryListView` (GET)

| Detail | Value |
|--------|-------|
| URL | `/products/categories/` |
| Name | `products:category_list` |
| Auth | Not required |
| Template | `products/category_list.html` |

Returns only **top-level** categories (`parent=None`) that are active.

---

## URL Configuration

```python
# products/urls.py
app_name = "products"

urlpatterns = [
    path("",                                    views.ProductListView.as_view(),  name="product_list"),
    path("category/<slug:category_slug>/",      views.ProductListView.as_view(),  name="category_detail"),
    path("product/<slug:slug>/",                views.ProductDetailView.as_view(), name="product_detail"),
    path("categories/",                         views.CategoryListView.as_view(), name="category_list"),
]
```

> **Note**: Both `product_list` and `category_detail` use the same `ProductListView`. The difference is that `category_detail` passes a `category_slug` URL kwarg which `get_queryset()` uses to filter.

---

## Admin

### `CategoryAdmin`
- `list_display`: name, slug, parent, display_order, is_active, created_at
- `list_editable`: display_order, is_active
- `prepopulated_fields`: slug from name
- `list_filter`: is_active, parent

### `TagAdmin`
- `list_display`: name, slug, is_active, created_at
- `prepopulated_fields`: slug from name

### `ProductAdmin`
- `list_display`: name, brand, sku, category, price, original_price, stock_quantity, availability_status, average_rating, review_count, is_active, created_at
- `list_editable`: price, stock_quantity, availability_status, is_active
- `prepopulated_fields`: slug from name
- `raw_id_fields`: category (for large category lists)
- `filter_horizontal`: tags (ManyToMany widget)
- `readonly_fields`: average_rating, review_count, created_at, updated_at
- **Fieldsets**: Identity, Description, Pricing, Stock & Availability, Media, Specifications, Ratings (collapsed), Timestamps (collapsed)

---

## How to Reuse This App in a New Project

1. **Copy the `products/` folder**.
2. Add `"products"` to `INSTALLED_APPS`.
3. Include URLs:
   ```python
   path("products/", include("products.urls")),
   ```
4. Run migrations:
   ```bash
   python manage.py makemigrations products
   python manage.py migrate
   ```
5. The `update_rating()` method imports from `reviews.models`. If you don't use the `reviews` app, remove that method and the `average_rating`/`review_count` fields.
6. The `specifications` JSONField requires a database that supports JSON (PostgreSQL) or SQLite 3.9+.
7. `image_gallery` is a JSONField storing a list of URL strings. If you need file uploads instead, replace it with a separate `ProductImage` model.

---

## Known Limitations & Future Improvements

- `image` (ImageField) is marked as "legacy" — the app uses `image_gallery` for URLs but keeps the old field for backward compatibility.
- No inventory decrement on order placement — `stock_quantity` must be updated manually via admin.
- `update_rating()` uses `Product.objects.filter(pk=...).update()` (avoids triggering `save()` again), which bypasses signals.
- The `specifications` JSONField has no schema validation — any dict is accepted.
