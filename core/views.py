from django.shortcuts import render
from django.contrib import messages
from products.models import Product, Category


def home(request):
    products = Product.objects.filter(is_available=True)[:8]
    categories = Category.objects.all()[:6]
    return render(request, "core/home.html", {
        "products": products,
        "categories": categories
    })


def about(request):
    return render(request, "core/about.html")


def contact(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        subject = request.POST.get("subject")
        message = request.POST.get("message")
        messages.success(request, f"Thank you {name}! Your message has been sent.")
        return render(request, "core/contact.html")
    return render(request, "core/contact.html")
