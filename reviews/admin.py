from django.contrib import admin
from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """Moderation-ready admin for user reviews."""
    list_display = [
        "product", "user", "rating", "title",
        "is_approved", "helpful_count", "created_at"
    ]
    list_filter = ["is_approved", "rating", "created_at"]
    list_editable = ["is_approved"]
    search_fields = ["product__name", "user__username", "title", "comment"]
    readonly_fields = ["created_at", "updated_at", "helpful_count"]
    actions = ["approve_reviews", "reject_reviews"]

    @admin.action(description="Approve selected reviews")
    def approve_reviews(self, request, queryset):
        queryset.update(is_approved=True)
        for review in queryset:
            review.product.update_rating()

    @admin.action(description="Reject selected reviews")
    def reject_reviews(self, request, queryset):
        queryset.update(is_approved=False)
        for review in queryset:
            review.product.update_rating()
