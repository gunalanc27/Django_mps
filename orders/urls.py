from django.urls import path
from . import views

app_name = "orders"

urlpatterns = [
    path("checkout/", views.checkout, name="checkout"),
    path("confirmation/<int:order_id>/", views.order_confirmation, name="order_confirmation"),
    path("orders/", views.order_list, name="order_list"),
    path("order/<int:order_id>/", views.order_detail, name="order_detail"),
]
