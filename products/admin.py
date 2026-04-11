from django.contrib import admin
from .models import Product, Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "created_at"] # what is this sliug and why it is needed 
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ["name"]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "price", "stock", "is_available", "created_at"]
    list_filter = ["category", "is_available", "created_at"]
    list_editable = ["price", "stock", "is_available"]
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ["name", "description"]
    raw_id_fields = ["category"]
