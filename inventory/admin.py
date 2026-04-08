from django.contrib import admin
from .models import Category, Product, InventoryLog

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'created_at')
    list_filter = ('company',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'sku', 'category', 'quantity', 'low_stock_threshold', 'is_low_stock')
    list_filter = ('company', 'category')
    search_fields = ('name', 'sku')

@admin.register(InventoryLog)
class InventoryLogAdmin(admin.ModelAdmin):
    list_display = ('product', 'action', 'quantity_changed', 'new_quantity', 'user', 'timestamp')
    list_filter = ('action', 'product__company')
    readonly_fields = ('timestamp',)