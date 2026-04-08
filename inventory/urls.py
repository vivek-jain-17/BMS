from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    path('', views.inventory_dashboard, name='dashboard'),
    path('add-category/', views.add_category, name='add_category'),
    path('add-product/', views.add_product, name='add_product'),
    path('update-stock/<int:product_id>/', views.update_stock, name='update_stock'),
    path('history/<int:product_id>/', views.product_history, name='product_history'),
    path('vendors/', views.vendor_list, name='vendor_list'),
    path('add-vendor/', views.add_vendor, name='add_vendor'),
    path('add-purchase/', views.add_purchase, name='add_purchase'),
]