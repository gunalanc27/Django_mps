import logging
from django.shortcuts import render, redirect
from django.contrib import messages
from products.models import Product, Category

logger = logging.getLogger(__name__)


def home(request):
    products = Product.objects.filter(is_active=True).order_by("-average_rating")[:8]
    categories = Category.objects.filter(is_active=True)[:6]
    return render(request, "core/home.html", {
        "products": products,
        "categories": categories
    })


def about(request):
    return render(request, "core/about.html")


def contact(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip()
        subject = request.POST.get("subject", "").strip()
        message = request.POST.get("message", "").strip()
        
        logger.info(f"Contact form submitted: {name} ({email}) - {subject}")
        # In a real app, send_mail() would be called here
        
        messages.success(request, f"Thank you {name}! Your message has been sent.")
        return redirect("core:contact")
        
    return render(request, "core/contact.html")


def partnership(request):
    if request.method == "POST":
        business_name = request.POST.get("business_name", "").strip()
        contact_person = request.POST.get("contact_person", "").strip()
        
        logger.info(f"Partnership inquiry: {business_name} (Contact: {contact_person})")
        
        messages.success(request, f"Thank you {contact_person}! Your partnership inquiry for {business_name} has been received. We will contact you shortly.")
        return redirect("core:partnership")
        
    return render(request, "core/partnership.html")
