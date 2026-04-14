from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from .models import Review
from products.models import Product


@login_required
def add_review(request, product_slug):
    product = get_object_or_404(Product, slug=product_slug)

    if request.method == "POST":
        try:
            rating = int(request.POST.get("rating", 0))
        except ValueError:
            rating = 0
            
        if rating not in [1, 2, 3, 4, 5]:
            messages.error(request, "Invalid rating value. Must be between 1 and 5.")
            return redirect(product.get_absolute_url())

        title = request.POST.get("title", "")
        comment = request.POST.get("comment")

        if Review.objects.filter(product=product, user=request.user).exists():
            messages.error(request, "You have already reviewed this product")
            return redirect(product.get_absolute_url())

        Review.objects.create(
            product=product,
            user=request.user,
            rating=rating,
            title=title,
            comment=comment,
        )
        messages.success(request, "Review submitted! It will appear after approval.")

    return redirect(product.get_absolute_url())


@login_required
def delete_review(request, review_id):
    review = get_object_or_404(Review, id=review_id)
    
    if request.user != review.user and not request.user.is_staff:
        return HttpResponseForbidden("You cannot delete this review")
    
    product_slug = review.product.slug
    review.delete()
    messages.success(request, "Review deleted")
    
    return redirect("products:product_detail", slug=product_slug)
