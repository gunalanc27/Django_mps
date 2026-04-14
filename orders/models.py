from django.db import models
from django.conf import settings
from products.models import Product

# just pass the models as the pararment then after hat define  multipchoice you want then after tht use the foreign key response then this is what happened
class Order(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("shipped", "Shipped"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="orders"
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    PAYMENT_CHOICES = [
        ("upi_qr", "UPI QR"),
    ]

    payment_method = models.CharField(max_length=50, choices=PAYMENT_CHOICES, default="upi_qr")
    is_paid = models.BooleanField(default=False)
    utr_number = models.CharField(max_length=100, blank=True, null=True)
    payment_screenshot = models.ImageField(upload_to="payment_proofs/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta: # what does this even do 
        ordering = ["-created_at"]

    def __str__(self): # this is a constructor right  fo rteuser  maping 
        return f"Order #{self.id} - {self.user.username}"


class OrderItem(models.Model): # now the thign is what is this and how does these values are stored on the database
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

    @property
    def get_total(self):
        return self.price * self.quantity
