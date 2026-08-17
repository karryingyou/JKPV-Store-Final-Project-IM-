from django.db import models

class Supplier(models.Model):
    name = models.CharField(max_length=100)
    contact_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name
    

class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.IntegerField(default=0)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Supplier field fixes the select_related crash
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.name

    @property
    def is_low_stock(self):
        """Returns True if stock quantity is 5 or less."""
        return self.stock_quantity <= 5

    @is_low_stock.setter
    def is_low_stock(self, value):
        """Safely ignores assignment attempts to prevent AttributeError."""
        pass


class Transaction(models.Model):
    PAYMENT_CHOICES = [
        ('Cash', 'Cash'),
        ('Gcash', 'GCash'),
        ('Utang', 'Utang'),
    ]

    payment_method = models.CharField(max_length=50, choices=PAYMENT_CHOICES, default='Cash')
    customer_name = models.CharField(max_length=200, blank=True, null=True)
    
    # NEW: Required to store the GCash reference number from the modal
    reference_number = models.CharField(max_length=100, blank=True, null=True, help_text="GCash Reference Number")
    
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_paid = models.BooleanField(default=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    date_paid = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Transaction {self.id} - {self.payment_method}"

    @property
    def items_summary(self):
        """Returns a string listing items in this transaction (e.g., '2x Coke, 1x Bread'). Needed for the dashboard."""
        return ", ".join([
            f"{item.quantity}x {item.product_name}" 
            for item in self.items.all()
        ])


class TransactionItem(models.Model):
    transaction = models.ForeignKey(Transaction, related_name='items', on_delete=models.CASCADE)
    product_name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField()

    def __str__(self):
        return f"{self.quantity}x {self.product_name}"

# Aliases for backward compatibility if your views/admin still reference Sale
Sale = Transaction
SaleItem = TransactionItem