import logging

from django.shortcuts import render, redirect, get_object_or_404
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


def checkout(request):
    cart = Cart(request)
    if not cart:
        messages.warning(request, "Your cart is empty!")
        return redirect("cart:cart_detail")

    if request.method == "POST":
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

        # Assign user only if authenticated; guests get None
        order_user = request.user if request.user.is_authenticated else None

        order = Order.objects.create(
            user=order_user,
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
            is_paid=True,
        )

        for item in cart:
            OrderItem.objects.create(
                order=order,
                product=item["product"],
                price=item["price"],
                quantity=item["quantity"],
            )

        if order.items.count() == 0:
            order.delete()
            messages.error(request, "Your cart appears to be empty or contains unavailable products.")
            return redirect("cart:cart_detail")

        # Build Google Sheets payload
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

        username = order.user.username if order.user else "Guest"
        payload = {
            "order_id":       order.id,
            "username":       username,
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

        # Store order id in session so guest can view confirmation
        request.session['last_order_id'] = order.id

        messages.success(request, f"Order #{order.id} placed successfully!")
        return redirect("orders:order_confirmation", order_id=order.id)

    context = {
        "cart": cart,
        "upi_id": settings.UPI_ID,
        "payee_name": settings.PAYEE_NAME,
    }
    return render(request, "orders/checkout.html", context)


def order_confirmation(request, order_id):
    """
    Allow both authenticated users (own orders) and guests (session-stored order id).
    """
    if request.user.is_authenticated:
        order = get_object_or_404(Order, id=order_id, user=request.user)
    else:
        # Guest: only show if it matches the order placed in this session
        session_order_id = request.session.get('last_order_id')
        if session_order_id != order_id:
            messages.error(request, "Order not found.")
            return redirect("core:home")
        order = get_object_or_404(Order, id=order_id, user__isnull=True)
    return render(request, "orders/order_confirmation.html", {"order": order})


def order_list(request):
    """
    Show orders only for logged-in users. Guests are redirected home.
    """
    if not request.user.is_authenticated:
        messages.info(request, "Please log in to view your order history.")
        return redirect("accounts:login")
    orders = Order.objects.filter(user=request.user)
    return render(request, "orders/order_list.html", {"orders": orders})


def order_detail(request, order_id):
    """
    Show order detail for logged-in users only. Guests are redirected.
    """
    if not request.user.is_authenticated:
        messages.info(request, "Please log in to view order details.")
        return redirect("accounts:login")
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, "orders/order_detail.html", {"order": order})
