from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.conf import settings
import requests
import threading
from cart.cart import Cart
from .models import Order, OrderItem


def _push_to_sheets(order):
    """
    Silently push order data to Google Sheets.
    Sends the Cloudinary image URL — no file reading needed.
    Runs in the background — user never sees this.
    """
    try:
        url = getattr(settings, 'GOOGLE_SCRIPT_URL', None)
        if not url:
            return

        # Get the Cloudinary URL for the screenshot (empty string if none uploaded)
        screenshot_url = ""
        if order.payment_screenshot:
            try:
                screenshot_url = order.payment_screenshot.url
            except Exception:
                screenshot_url = ""

        payload = {
            "order_id":          order.id,
            "username":          order.user.username,
            "name":              f"{order.first_name} {order.last_name}",
            "email":             order.email,
            "phone":             order.phone,
            "address":           order.address,
            "city":              order.city,
            "state":             order.state,
            "postal_code":       order.postal_code,
            "country":           order.country,
            "total_amount":      str(order.total_amount),
            "screenshot_url":    screenshot_url,
            "is_paid":           order.is_paid,
            "utr_number":        order.utr_number or "",
            "created_at":        order.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        }

        requests.post(url, json=payload, timeout=10)

    except Exception:
        pass  # Silently ignore — never surface errors to the user


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
        payment_method = request.POST.get("payment_method", "upi")
        utr_number = request.POST.get("utr_number")
        payment_screenshot = request.FILES.get("payment_screenshot")

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
            payment_method=payment_method,
            utr_number=utr_number,
            payment_screenshot=payment_screenshot,
        )

        for item in cart:
            OrderItem.objects.create(
                order=order,
                product=item["product"],
                price=item["price"],
                quantity=item["quantity"],
            )

        cart.clear()
        # Silent background sync to Google Sheets (user never sees this)
        threading.Thread(target=_push_to_sheets, args=(order,), daemon=True).start()
        messages.success(request, f"Order #{order.id} placed successfully!")
        return redirect("orders:order_confirmation", order_id=order.id)

    context = {
        "cart": cart,
        "upi_id": settings.UPI_ID,
        "payee_name": settings.PAYEE_NAME,
    }
    return render(request, "orders/checkout.html", context)


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
