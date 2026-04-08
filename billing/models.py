from django.db import models
from accounts.models import Company
from bms import settings
from bms import settings
from inventory.models import Product, InventoryLog
import uuid

# 1. CLIENT MODEL (CRM Base)
class Client(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='clients')
    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    tax_number = models.CharField(max_length=50, blank=True, null=True, help_text="GST/VAT Number")
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

# 2. INVOICE MODEL (Main Billing Record)
class Invoice(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('paid', 'Paid'),
        ('unpaid', 'Unpaid'),
        ('overdue', 'Overdue'),
    )

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='invoices')
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='invoices')
    
    invoice_number = models.CharField(max_length=50) # Example: INV-2026-001
    date = models.DateField()
    due_date = models.DateField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='created_invoices'
    )    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Financials
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    tax_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    # Auto-Deduction Flag (Taaki ek invoice 2 baar stock deduct na kare)
    inventory_deducted = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('company', 'invoice_number') # Har company ka invoice number unique hoga

    def __str__(self):
        return f"{self.invoice_number} - {self.client.name}"

    # THE MAGIC METHOD: Auto-Deduct Inventory
    def deduct_inventory(self, user):
        if not self.inventory_deducted:
            for item in self.items.all():
                product = item.product
                if product:
                    previous_qty = product.quantity
                    # Stock kam karo
                    product.quantity -= item.quantity
                    product.save()
                    
                    # Inventory History/Log generate karo (Teri requirement!)
                    InventoryLog.objects.create(
                        product=product,
                        user=user,
                        action='OUT',
                        quantity_changed=-item.quantity,
                        previous_quantity=previous_qty,
                        new_quantity=product.quantity,
                        notes=f"Sold via Invoice {self.invoice_number}"
                    )
            
            # Flag ko True kardo taaki dobara stock deduct na ho
            self.inventory_deducted = True
            self.save()


# 3. INVOICE ITEM MODEL (Line Items)
class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True) # Agar product delete ho jaye, bill kharab na ho
    
    description = models.CharField(max_length=255) # Custom description agar product na ho
    quantity = models.PositiveIntegerField(default=1)
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    amount = models.DecimalField(max_digits=12, decimal_places=2) # quantity * rate

    def __str__(self):
        return f"{self.quantity} x {self.description}"


# 4. ESTIMATE / QUOTATION MODEL
class Estimate(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    )
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='estimates')
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='estimates')
    estimate_number = models.CharField(max_length=50)
    date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"EST-{self.estimate_number} - {self.client.name}"