from django.db import models
from django.conf import settings
from products.models import Product


class Review(models.Model):
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = ["product", "user"]

    def __str__(self):
        return f"{self.user.username} - {self.product.name} ({self.rating})"

    @property
    def average_rating(self):
        return self.rating
