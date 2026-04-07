from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from cart.cart import Cart
from .models import Order, OrderItem


@login_required
def checkout(request):
    cart = Cart(request)
    if not cart:
        messages.warning(request, "Your cart is empty!")
        return redirect("cart:cart_detail")

    if request.method == "POST":
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        address = request.POST.get("address")
        city = request.POST.get("city")
        state = request.POST.get("state")
        postal_code = request.POST.get("postal_code")
        country = request.POST.get("country")

        order = Order.objects.create(
            user=request.user,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            address=address,
            city=city,
            state=state,
            postal_code=postal_code,
            country=country,
            total_amount=cart.get_total_price(),
        )

        for item in cart:
            OrderItem.objects.create(
                order=order,
                product=item["product"],
                price=item["price"],
                quantity=item["quantity"],
            )

        cart.clear()
        messages.success(request, f"Order #{order.id} placed successfully!")
        return redirect("orders:order_confirmation", order_id=order.id)

    return render(request, "orders/checkout.html", {"cart": cart})


@login_required
def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, "orders/order_confirmation.html", {"order": order})


@login_required
def order_list(request):
    orders = Order.objects.filter(user=request.user)
    return render(request, "orders/order_list.html", {"orders": orders})


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, "orders/order_detail.html", {"order": order})
