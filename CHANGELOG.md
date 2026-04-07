# Development Changelog

All notable changes to the django_Learn (Vajra) project are documented here.

## [Unreleased]

### Added - E-Commerce Application
- **core** app: Home, About, Contact pages
- **products** app: Product catalog with categories, search, filtering
- **cart** app: Shopping cart with session-based storage
- **orders** app: Checkout flow, order management
- **accounts** app: User registration, login, profile
- **reviews** app: Product reviews and ratings system
- **base.html**: Base template with Bootstrap 5 navbar
- **static/ & media/**: Static and media directories
- **Pillow**: Installed for image field support

### Configured
- **Django Debug Toolbar** (v6.3.0)
- **TEMPLATE_DIRS**: Added templates directory
- **MEDIA_URL/MEDIA_ROOT**: For product images
- **CART_SESSION_ID**: Session-based cart configuration
- **URL routing**: All apps connected to main urls.py

### Models Created
- **Category**: Product categories with slugs
- **Product**: Products with name, price, stock, image
- **Order**: Customer orders with shipping info
- **OrderItem**: Individual items in orders
- **Review**: Product reviews with ratings (1-5)

---

## Project History

### 2026-04-06 - E-Commerce Build
- Created 6 Django apps (core, products, cart, orders, accounts, reviews)
- Built full CRUD functionality for all apps
- Created responsive templates with Bootstrap 5
- Ran migrations successfully
- System check passed

### 2026-04-06 - Initial Setup
- Initial project setup with Django 6.0.3
- Created `Vajra` main project
- Created `accounts` app with basic structure
- Configured SQLite database (db.sqlite3)
- Set up virtual environment (Dvenv/) with Python 3.13
- Installed django-debug-toolbar

---

## Notes for Developers

### Adding New Changes
1. Document the change in this file with date
2. Include affected files/components
3. Note any breaking changes
4. Update related documentation

### Change Types
- **Added**: New features or files
- **Changed**: Modifications to existing functionality
- **Deprecated**: Soon-to-be removed features
- **Removed**: Removed features
- **Fixed**: Bug fixes
- **Security**: Vulnerability fixes
- **Config**: Configuration changes
