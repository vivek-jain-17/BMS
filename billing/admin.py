from django.contrib import admin
from .models import Client, Invoice, InvoiceItem, Estimate

class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'company')
    search_fields = ('name', 'email')

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'client', 'date', 'status', 'total_amount', 'inventory_deducted')
    list_filter = ('status', 'company')
    inlines = [InvoiceItemInline]

@admin.register(Estimate)
class EstimateAdmin(admin.ModelAdmin):
    list_display = ('estimate_number', 'client', 'status', 'total_amount')