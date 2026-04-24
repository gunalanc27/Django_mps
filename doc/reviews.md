# App: `reviews`

## Overview

The `reviews` app provides a product review system with **moderation**. Users can submit a star rating (1–5) and optional text review for any product. Reviews are hold by default (`is_approved=False`) and must be approved by an admin before they become visible. Every save or delete of a review triggers an automatic recalculation of the parent product's `average_rating` and `review_count` fields.

**App namespace**: `reviews`  
**URL prefix** (as registered in `tes/urls.py`): `/reviews/`

---

## Files

```
reviews/
├── __init__.py
├── admin.py    — ReviewAdmin (moderation interface)
├── apps.py     — AppConfig (name = "reviews")
├── models.py   — Review
├── tests.py    — placeholder
├── urls.py     — URL routing
└── views.py    — add_review, delete_review
```

> **Note**: The `reviews` app has no templates of its own. The review submission form is rendered inside `products/product_detail.html`, and all views redirect back to the product detail page after action.

---

## Models

### `Review`

A single user review for a product.

| Field | Type | Notes |
|-------|------|-------|
| `product` | ForeignKey(Product) | CASCADE; `related_name="reviews"` |
| `user` | ForeignKey(AUTH_USER_MODEL) | CASCADE |
| `rating` | PositiveSmallIntegerField | Choices: 1–5 |
| `title` | CharField(200) | Optional review headline |
| `comment` | TextField | Required review body |
| `is_approved` | BooleanField | Default `False` — reviews are hidden until approved by admin |
| `helpful_count` | IntegerField | Default 0; can be incremented by a "helpful?" feature (not yet implemented in views) |
| `created_at` | DateTimeField | Auto |
| `updated_at` | DateTimeField | Auto |

**Ordering**: `["-created_at"]` (newest first)

**Unique constraint**: `unique_together = ["product", "user"]` — each user can only review a product once.

**`__str__`**: `"<username> — <product name> (<rating>★)"`

---

### Model Signals (via `save()` and `delete()`)

Rather than using Django signals, the aggregate recalculation is hooked directly into the model's `save()` and `delete()` methods:

```python
def save(self, *args, **kwargs):
    super().save(*args, **kwargs)
    self.product.update_rating()   # ← recalculate average_rating + review_count

def delete(self, *args, **kwargs):
    product = self.product          # ← capture before deletion
    super().delete(*args, **kwargs)
    product.update_rating()
```

> **Important**: `product` must be captured **before** calling `super().delete()` because after deletion, `self.product` may raise a `RelatedObjectDoesNotExist` error.

The `update_rating()` method lives on `Product` (in `products/models.py`) to keep the database round-trip in one place:
```python
def update_rating(self):
    from reviews.models import Review   # lazy import
    approved = Review.objects.filter(product=self, is_approved=True)
    count = approved.count()
    avg = approved.aggregate(Avg("rating"))["rating__avg"] or 0.00
    Product.objects.filter(pk=self.pk).update(
        average_rating=round(avg, 2),
        review_count=count,
    )
```

This uses `.update()` instead of `.save()` to avoid triggering `Product.save()` again (which would auto-generate slug/SKU and mark the session as modified unnecessarily).

---

## Views

Both views are **function-based views (FBVs)** with `@login_required`.

### `add_review` (POST only — redirects on GET)

| Detail | Value |
|--------|-------|
| URL | `/reviews/add/<slug:product_slug>/` |
| Name | `reviews:add_review` |
| Auth | Required |
| Template | None (redirects to product detail) |

**Flow:**
1. Fetch product by slug (`get_object_or_404`).
2. Parse `rating` from POST; validate it's an integer between 1 and 5. If invalid, show error and redirect.
3. Read `title` and `comment`.
4. Check for existing review by this user for this product (`unique_together`). If duplicate, show error and redirect.
5. Create the `Review` (triggers `save()` → `update_rating()`).
6. Show success message: *"Review submitted! It will appear after approval."*
7. Redirect to `product.get_absolute_url()`.

**Why no custom template?** The submission form is embedded directly in `products/product_detail.html`. Responses redirect back there, keeping the UX linear.

**HTML form pattern in `product_detail.html`:**
```html
<form method="post" action="{% url 'reviews:add_review' product.slug %}">
  {% csrf_token %}
  <input type="number" name="rating" min="1" max="5" required>
  <input type="text" name="title" placeholder="Headline (optional)">
  <textarea name="comment" required></textarea>
  <button type="submit">Submit Review</button>
</form>
```

---

### `delete_review` (POST redirect)

| Detail | Value |
|--------|-------|
| URL | `/reviews/delete/<int:review_id>/` |
| Name | `reviews:delete_review` |
| Auth | Required |
| Template | None (redirects to product detail) |

**Authorization check:**
```python
if request.user != review.user and not request.user.is_staff:
    return HttpResponseForbidden("You cannot delete this review")
```

Only the review's author or a staff member can delete it.

**Flow after auth check:**
1. Capture `product_slug = review.product.slug` before deletion.
2. Delete the review (triggers `delete()` → `update_rating()`).
3. Show success message.
4. Redirect to `products:product_detail` using the captured slug.

---

## URL Configuration

```python
# reviews/urls.py
app_name = "reviews"

urlpatterns = [
    path("add/<slug:product_slug>/",   views.add_review,    name="add_review"),
    path("delete/<int:review_id>/",    views.delete_review, name="delete_review"),
]
```

---

## Admin

### `ReviewAdmin`

A moderation-focused interface.

| Setting | Value |
|---------|-------|
| `list_display` | product, user, rating, title, is_approved, helpful_count, created_at |
| `list_filter` | is_approved, rating, created_at |
| `list_editable` | is_approved (toggle directly in list view) |
| `search_fields` | product\_\_name, user\_\_username, title, comment |
| `readonly_fields` | created_at, updated_at, helpful_count |

**Bulk Actions:**

| Action | Effect |
|--------|--------|
| `approve_reviews` | Sets `is_approved=True`; calls `review.product.update_rating()` for each |
| `reject_reviews` | Sets `is_approved=False`; calls `update_rating()` for each |

> **Caution with bulk approve**: The admin action calls `update_rating()` in a Python loop, which can be slow for large querysets. For high-volume stores, consider a signal-based or Celery task-based approach instead.

---

## Dependencies

| Dependency | Why |
|------------|-----|
| `products.models.Product` | Reviews are linked to products via FK |
| `settings.AUTH_USER_MODEL` | Reviews are linked to users |

---

## How to Reuse This App in a New Project

1. **Copy the `reviews/` folder**.
2. Add `"reviews"` to `INSTALLED_APPS`.
3. Include URLs:
   ```python
   path("reviews/", include("reviews.urls")),
   ```
4. Run migrations:
   ```bash
   python manage.py makemigrations reviews
   python manage.py migrate
   ```
5. Add `average_rating` (DecimalField) and `review_count` (IntegerField) to your product model, plus the `update_rating()` method:
   ```python
   def update_rating(self):
       from reviews.models import Review
       approved = Review.objects.filter(product=self, is_approved=True)
       count = approved.count()
       avg = approved.aggregate(models.Avg("rating"))["rating__avg"] or 0.00
       YourProduct.objects.filter(pk=self.pk).update(
           average_rating=round(avg, 2),
           review_count=count,
       )
   ```
6. Embed the review submission form and review list in your product detail template.
7. Use `{% url 'reviews:add_review' product.slug %}` for the form action.
8. Display only approved reviews:
   ```python
   Review.objects.filter(product=product, is_approved=True)
   ```

---

## Known Limitations & Future Improvements

- No "helpful" voting endpoint exists — `helpful_count` is stored but cannot be incremented by users from the current UI.
- No edit review feature — users can only submit or delete.
- Admin `approve_reviews` action triggers N individual `update_rating()` calls — could be optimized with a bulk recalculation.
- Reviews require admin approval, which adds latency. Consider an auto-approve path for verified purchasers.
- No email notification to the product submitter or admin when a new review arrives.
