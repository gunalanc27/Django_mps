from django.contrib import admin
from .models import Product, Category, Tag


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "parent", "display_order", "is_active", "created_at"]
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ["name", "description"]
    list_filter = ["is_active", "parent"]
    list_editable = ["display_order", "is_active"]
    ordering = ["display_order", "name"]


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "is_active", "created_at"]
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ["name", "description"]
    list_filter = ["is_active"]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        "name", "brand", "sku", "category",
        "price", "original_price", "stock_quantity",
        "availability_status", "average_rating", "review_count",
        "is_active", "created_at",
    ]
    list_filter = ["category", "availability_status", "is_active", "brand", "created_at"]
    list_editable = ["price", "stock_quantity", "is_active"]
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ["name", "brand", "sku", "model_number", "short_description"]
    raw_id_fields = ["category"]
    filter_horizontal = ["tags"]
    readonly_fields = ["average_rating", "review_count", "created_at", "updated_at"]
    fieldsets = (
        ("Identity", {
            "fields": ("name", "slug", "sku", "brand", "model_number", "category", "tags")
        }),
        ("Description", {
            "fields": ("short_description", "long_description")
        }),
        ("Pricing", {
            "fields": ("price", "original_price", "currency")
        }),
        ("Stock & Availability", {
            "description": "Set stock_quantity. availability_status auto-syncs: 0 → Out of Stock, >0 → In Stock. Set Pre-Order or Discontinued manually to bypass auto-sync.",
            "fields": ("stock_quantity", "availability_status", "is_active")
        }),
        ("Media", {
            "fields": ("image", "image_gallery", "video_url")
        }),
        ("Specifications", {
            "fields": ("specifications",)
        }),
        ("Ratings (Read Only)", {
            "fields": ("average_rating", "review_count"),
            "classes": ("collapse",)
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )
