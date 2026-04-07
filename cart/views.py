from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from products.models import Product
from .cart import Cart


@require_POST
def add_to_cart(request, slug):
    cart = Cart(request)
    product = get_object_or_404(Product, slug=slug)
    quantity = int(request.POST.get("quantity", 1))
    cart.add(product, quantity)
    return redirect("cart:cart_detail")


@require_POST
def update_cart(request, product_id):
    cart = Cart(request)
    quantity = int(request.POST.get("quantity", 1))
    if quantity > 0:
        cart.update(product_id, quantity)
    else:
        cart.remove(product_id)
    return redirect("cart:cart_detail")


@require_POST
def remove_from_cart(request, slug):
    cart = Cart(request)
    product = get_object_or_404(Product, slug=slug)
    cart.remove(product.id)
    return redirect("cart:cart_detail")


def cart_detail(request):
    cart = Cart(request)
    return render(request, "cart/cart_detail.html", {"cart": cart})


@require_POST
def clear_cart(request):
    cart = Cart(request)
    cart.clear()
    return redirect("cart:cart_detail")
