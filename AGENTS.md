# Agent Guidelines for django_Learn

## Project Overview
- **Project**: Vajra (Django Learning Project)
- **Framework**: Django 6.0.3
- **Database**: SQLite (db.sqlite3)
- **Virtual Environment**: Dvenv/
- **Python Version**: 3.13

## Project Structure
```
django_Learn/
├── manage.py              # Django management script
├── db.sqlite3             # SQLite database
├── Dvenv/                 # Virtual environment
├── Vajra/                 # Main Django project
│   ├── settings.py        # Settings configuration
│   ├── urls.py            # Root URL configuration
│   ├── wsgi.py            # WSGI application
│   └── asgi.py            # ASGI application
├── accounts/              # Accounts app
│   ├── models.py          # Database models
│   ├── views.py           # View functions
│   ├── tests.py           # Unit tests
│   ├── admin.py           # Admin configuration
│   ├── urls.py            # App URLs
│   └── templates/         # App templates
└── blog/                  # Blog app
    └── ...
```

## Build/Lint/Test Commands

### Django Management
```bash
# Activate virtual environment
source Dvenv/bin/activate

# Run development server
python manage.py runserver

# Check for issues
python manage.py check

# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Shell access
python manage.py shell
```

### Running Tests
```bash
# Run all tests
python manage.py test

# Run tests for specific app
python manage.py test accounts

# Run specific test class
python manage.py test accounts.TestClassName

# Run specific test method
python manage.py test accounts.TestClassName.test_method_name
```

### Code Quality
```bash
# Format code (if black installed)
black .

# Lint code (if flake8 installed)
flake8 .

# Type checking (if mypy installed)
mypy .
```

## Code Style Guidelines

### General Rules
1. **Line Length**: Keep lines under 120 characters
2. **Indentation**: Use 4 spaces (not tabs)
3. **Blank Lines**: Two blank lines between top-level definitions
4. **File Encoding**: UTF-8

### Import Conventions (PEP 8)
```python
# Standard library
import os
import sys
from pathlib import Path

# Third-party packages
from django.db import models
from django.http import HttpResponse

# Local imports
from .models import MyModel
from .views import my_view

# Ordering: stdlib → third-party → local (with blank lines between)
```

### Naming Conventions
| Type | Convention | Example |
|------|------------|---------|
| Classes | PascalCase | `UserProfile`, `BlogPost` |
| Functions | snake_case | `get_user()`, `create_post()` |
| Variables | snake_case | `user_data`, `post_list` |
| Constants | UPPER_SNAKE_CASE | `MAX_RETRIES`, `API_URL` |
| Private vars | _leading_underscore | `_private_method()` |
| Django Models | PascalCase | `class Post(models.Model)` |
| Django URLs | kebab-case in URLs, snake_case in views | `/blog/post-detail/` |

### Django-Specific Guidelines

#### Models
```python
from django.db import models

class Post(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_published = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Blog Post'
        verbose_name_plural = 'Blog Posts'
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('post_detail', kwargs={'pk': self.pk})
```

#### Views
```python
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin

# Function-based view
def post_list(request):
    posts = Post.objects.all()
    return render(request, 'blog/post_list.html', {'posts': posts})

# Class-based view
class PostDetailView(LoginRequiredMixin, View):
    def get(self, request, pk):
        post = get_object_or_404(Post, pk=pk)
        return render(request, 'blog/post_detail.html', {'post': post})
```

#### URLs
```python
from django.urls import path
from . import views

app_name = 'blog'  # Namespace for the app

urlpatterns = [
    path('', views.post_list, name='post_list'),
    path('<int:pk>/', views.post_detail, name='post_detail'),
]
```

### Error Handling
```python
# Django exceptions
from django.http import Http404
from django.shortcuts import get_object_or_404

# Always use get_object_or_404 for single object retrieval
post = get_object_or_404(Post, pk=pk)

# Custom error handling
try:
    result = risky_operation()
except SpecificError as e:
    logger.error(f"Error occurred: {e}")
    raise Http404("Resource not found")
```

### Docstrings
```python
def calculate_total(items):
    """
    Calculate the total price of items in the cart.
    
    Args:
        items: QuerySet of CartItem objects
        
    Returns:
        Decimal: Total price rounded to 2 decimal places
    """
    return sum(item.price for item in items)
```

## Configuration Requirements

### Debug Toolbar
When adding debug_toolbar:
1. Add `'debug_toolbar'` to INSTALLED_APPS
2. Add `'debug_toolbar.middleware.DebugToolbarMiddleware'` to MIDDLEWARE (near top)
3. Add `INTERNAL_IPS = ['127.0.0.1']` to settings
4. Add to urls.py: `path('__debug__/', include('debug_toolbar.urls'))`

### Environment Variables
Never commit secrets. Use environment variables:
```python
import os
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
DEBUG = os.environ.get('DEBUG', 'False') == 'True'
```

## Testing Best Practices
```python
from django.test import TestCase
from django.urls import reverse

class PostModelTest(TestCase):
    def setUp(self):
        self.post = Post.objects.create(title='Test', content='Content')
    
    def test_str_representation(self):
        self.assertEqual(str(self.post), 'Test')
    
    def test_create_view(self):
        response = self.client.get(reverse('blog:post_create'))
        self.assertEqual(response.status_code, 200)
```
