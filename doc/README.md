# Project Documentation Index

This folder contains detailed developer documentation for every Django application in the **tes** project. Each file covers models, views, URLs, forms, admin configuration, design decisions, and reuse guidance.

## Applications

| File | App | Purpose |
|------|-----|---------|
| [accounts.md](./accounts.md) | `accounts` | User registration, login, logout, profile |
| [cart.md](./cart.md) | `cart` | Session-based shopping cart |
| [core.md](./core.md) | `core` | Homepage, about, contact, partnership pages |
| [products.md](./products.md) | `products` | Product catalogue, categories, tags |
| [orders.md](./orders.md) | `orders` | Checkout, order management, Google Sheets sync |
| [reviews.md](./reviews.md) | `reviews` | Product reviews with moderation |
| [project_settings.md](./project_settings.md) | `tes` (project) | Settings, middleware, storage, third-party integrations |

## Dependency Graph

```
core  ──────────────────────────►  products
cart  ──────────────────────────►  products
orders  ────────────────────────►  products, cart
reviews  ───────────────────────►  products
products  ──────────────────────►  reviews (circular — via update_rating())
accounts  ──────────────────────►  (no app dependencies; uses Django auth)
```

> **Note on circular import**: `products.models.Product.update_rating()` imports `reviews.models.Review` inside the method body (lazy import) to avoid a circular import at module load time. If you refactor, keep this pattern.

## Project Stack

- **Django**: 6.0.3
- **Database**: SQLite (dev) / PostgreSQL via `DATABASE_URL` (prod)
- **Media Storage**: Cloudinary (`django-cloudinary-storage`)
- **Static Files**: WhiteNoise (production) / Django default (development)
- **Admin UI**: Jazzmin
- **CSS**: Tailwind CSS (via `django-tailwind`)
- **Deployment**: Vercel
