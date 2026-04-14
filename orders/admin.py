from django.contrib import admin
from .models import Order, OrderItem

# wha ddoes that even mean 
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ["product", "price", "quantity"]


# what is the differnce btw the two of them 

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "first_name", "last_name", "total_amount", "status", "created_at"]
    list_filter = ["status", "created_at"]
    search_fields = ["first_name", "last_name", "email", "id"]
    list_per_page = 25
    inlines = [OrderItemInline]
    actions = ["mark_confirmed", "mark_shipped", "mark_delivered", "mark_cancelled"]

    @admin.action(description="Mark selected orders as Confirmed")
    def mark_confirmed(self, request, queryset):
        queryset.update(status="confirmed")

    @admin.action(description="Mark selected orders as Shipped")
    def mark_shipped(self, request, queryset):
        queryset.update(status="shipped")

    @admin.action(description="Mark selected orders as Delivered")
    def mark_delivered(self, request, queryset):
        queryset.update(status="delivered")

    @admin.action(description="Mark selected orders as Cancelled")
    def mark_cancelled(self, request, queryset):
        queryset.update(status="cancelled")


