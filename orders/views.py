import logging

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
import requests
import threading
from cart.cart import Cart
from .models import Order, OrderItem

logger = logging.getLogger(__name__)


def _push_to_sheets(payload):
    """
    Silently push order data to Google Sheets in the background.
    Runs in a daemon thread — user never sees this.
    """
    try:
        url = getattr(settings, 'GOOGLE_SCRIPT_URL', None)
        if not url:
            return
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        logger.warning(f"Google Sheets sync failed for order {payload.get('order_id')}: {e}")


@login_required
def checkout(request):
    cart = Cart(request)
    if not cart:
        messages.warning(request, "Your cart is empty!")
        return redirect("cart:cart_detail")

    if request.method == "POST":
        # --- BUG-02: Server-side field validation ---
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        email = request.POST.get("email", "").strip()
        phone = request.POST.get("phone", "").strip()
        address = request.POST.get("address", "").strip()
        city = request.POST.get("city", "").strip()
        state = request.POST.get("state", "").strip()
        postal_code = request.POST.get("postal_code", "").strip()
        country = request.POST.get("country", "").strip()
        payment_method = request.POST.get("payment_method", "upi_qr")
        utr_number = request.POST.get("utr_number", "").strip()
        payment_screenshot = request.FILES.get("payment_screenshot")

        required_fields = {
            "First Name": first_name,
            "Last Name": last_name,
            "Email": email,
            "Phone": phone,
            "Address": address,
            "City": city,
            "State": state,
            "Postal Code": postal_code,
            "Country": country,
            "UTR Number": utr_number,
        }
        missing = [label for label, value in required_fields.items() if not value]
        if missing:
            messages.error(request, f"Missing required fields: {', '.join(missing)}")
            context = {"cart": cart, "upi_id": settings.UPI_ID, "payee_name": settings.PAYEE_NAME}
            return render(request, "orders/checkout.html", context)

        if not payment_screenshot:
            messages.error(request, "Payment screenshot is required.")
            context = {"cart": cart, "upi_id": settings.UPI_ID, "payee_name": settings.PAYEE_NAME}
            return render(request, "orders/checkout.html", context)

        # --- BUG-01: is_paid=True since screenshot + UTR are provided ---
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
            is_paid=True,  # Screenshot + UTR submitted — treat as paid pending admin review
        )

        for item in cart:
            OrderItem.objects.create(
                order=order,
                product=item["product"],
                price=item["price"],
                quantity=item["quantity"],
            )

        # --- BUG-03: Guard against empty cart / deleted products ---
        if order.items.count() == 0:
            order.delete()
            messages.error(request, "Your cart appears to be empty or contains unavailable products.")
            return redirect("cart:cart_detail")

        # --- Build Google Sheets Payload ---
        screenshot_url = ""
        if order.payment_screenshot:
            try:
                screenshot_url = order.payment_screenshot.url
            except Exception:
                screenshot_url = ""

        products_str = ""
        try:
            items = list(order.items.all())
            products_list = []
            for item in items:
                p = item.product
                sku_str = p.sku or "N/A"
                brand_str = p.brand or "N/A"
                products_list.append(f"{p.name} (SKU: {sku_str}, Brand: {brand_str}) - Qty: {item.quantity}")
            products_str = " | ".join(products_list)
        except Exception as e:
            logger.warning(f"Could not build products string for order {order.id}: {e}")

        payload = {
            "order_id":       order.id,
            "username":       order.user.username,
            "name":           f"{order.first_name} {order.last_name}",
            "email":          order.email,
            "phone":          order.phone,
            "address":        order.address,
            "city":           order.city,
            "state":          order.state,
            "postal_code":    order.postal_code,
            "country":        order.country,
            "total_amount":   str(order.total_amount),
            "products":       products_str,
            "screenshot_url": screenshot_url,
            "is_paid":        order.is_paid,
            "utr_number":     order.utr_number or "",
            "created_at":     order.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        }

        cart.clear()
        threading.Thread(target=_push_to_sheets, args=(payload,), daemon=True).start()

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
