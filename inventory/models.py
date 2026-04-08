from django.db import models
from accounts.models import Company, User

# 1. CATEGORY MODEL (Category-wise inventory view ke liye)
class Category(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Ek company mein same naam ki 2 categories nahi ho sakti
        unique_together = ('company', 'name')

    def __str__(self):
        return self.name


# 2. PRODUCT MODEL (Core inventory items)
class Product(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='products')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=100, help_text="Stock Keeping Unit / Barcode")
    description = models.TextField(blank=True, null=True)
    
    # Stock Tracking
    quantity = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(default=10, help_text="Alert if stock goes below this")
    
    # Pricing (Optional but good to have)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    # NAYA FIELD: Kharid ka bhav (Sensitive Info)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Har company ka SKU unique hona chahiye
        unique_together = ('company', 'sku')

    def __str__(self):
        return f"{self.name} (SKU: {self.sku})"
    
    # Helper property checking for alerts
    @property
    def is_low_stock(self):
        return self.quantity <= self.low_stock_threshold


# 3. INVENTORY LOG MODEL (Product Full History tracking ke liye)
class InventoryLog(models.Model):
    ACTION_CHOICES = [
        ('IN', 'Stock In (Purchase/Added)'),
        ('OUT', 'Stock Out (Sold/Used)'),
        ('ADJ', 'Adjustment (Lost/Damaged/Found)'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_history')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, help_text="Who made the change")
    
    action = models.CharField(max_length=5, choices=ACTION_CHOICES)
    quantity_changed = models.IntegerField(help_text="Can be positive or negative")
    
    # Reference ke liye previous aur new quantity save karenge
    previous_quantity = models.PositiveIntegerField()
    new_quantity = models.PositiveIntegerField()
    
    notes = models.CharField(max_length=255, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.name} | {self.get_action_display()} | {self.quantity_changed} by {self.user.first_name}"
    



class Vendor(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='vendors')
    name = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

# 5. PURCHASE RECORD MODEL (Maal aane ka record)
class PurchaseRecord(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='purchases')
    vendor = models.ForeignKey(Vendor, on_delete=models.SET_NULL, null=True, related_name='purchases')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='purchases')
    
    quantity = models.PositiveIntegerField()
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, help_text="Jis rate pe abhi kharida")
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, editable=False)
    
    reference_number = models.CharField(max_length=100, blank=True, null=True, help_text="Vendor ka Bill/Invoice Number")
    purchase_date = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Auto calculate total cost before saving
        self.total_cost = self.quantity * self.unit_cost
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Bought {self.quantity} {self.product.name} from {self.vendor.name}"