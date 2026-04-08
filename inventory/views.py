from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Product, Category, InventoryLog

@login_required
def inventory_dashboard(request):
    # Sirf us company ka data fetch karo jiska user hai
    company = request.user.company
    
    products = Product.objects.filter(company=company).order_by('name')
    categories = Category.objects.filter(company=company)
    
    # Category filter apply karna (agar URL mein ?category=id aaya hai)
    category_id = request.GET.get('category')
    if category_id:
        products = products.filter(category_id=category_id)

    # Low stock calculate karna
    # Hum Python mein filter kar rahe hain kyunki is_low_stock ek property hai
    low_stock_products = [p for p in products if p.is_low_stock]
    
    stats = {
        'total_products': products.count(),
        'total_categories': categories.count(),
        'low_stock_count': len(low_stock_products),
        'total_value': sum(p.quantity * p.unit_price for p in products)
    }

    # HTMX Dynamic Base Trick
    base_template = 'shared/base.html' if request.headers.get('HX-Request') else 'shared/base.html'

    context = {
        'products': products,
        'categories': categories,
        'stats': stats,
        'active_category': int(category_id) if category_id else None,
        'base_template': base_template,
        'page_title': 'Inventory Management'
    }
    
    return render(request, 'inventory/dashboard.html', context)


from django.http import HttpResponse
from .forms import CategoryForm, ProductForm
from .models import Product, Category, InventoryLog

# --- ADD CATEGORY ---
@login_required
def add_category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.company = request.user.company
            category.save()
            
            # HTMX Trigger bhej rahe hain table refresh karne ke liye
            response = HttpResponse()
            response['HX-Trigger'] = 'inventoryRefresh'
            return response
    else:
        form = CategoryForm()
        
    return render(request, 'inventory/partials/modal_form.html', {'form': form, 'title': 'Add New Category', 'url': reverse('inventory:add_category')})

# --- ADD PRODUCT ---
@login_required
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, company=request.user.company)
        if form.is_valid():
            product = form.save(commit=False)
            product.company = request.user.company
            product.save()
            
            # Agar add karte waqt quantity > 0 hai, toh pehla log create karo
            if product.quantity > 0:
                InventoryLog.objects.create(
                    product=product, user=request.user, action='IN',
                    quantity_changed=product.quantity, previous_quantity=0, new_quantity=product.quantity,
                    notes="Initial Stock added"
                )
                
            response = HttpResponse()
            response['HX-Trigger'] = 'inventoryRefresh'
            return response
    else:
        form = ProductForm(company=request.user.company)
        
    return render(request, 'inventory/partials/modal_form.html', {'form': form, 'title': 'Add New Product', 'url': reverse('inventory:add_product')})

# --- UPDATE STOCK (WITH LOGGING) ---
@login_required
def update_stock(request, product_id):
    product = get_object_or_404(Product, id=product_id, company=request.user.company)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        quantity_changed = int(request.POST.get('quantity', 0))
        notes = request.POST.get('notes', '')
        
        previous_quantity = product.quantity
        
        # Quantity calculate karo
        if action == 'IN':
            product.quantity += quantity_changed
        elif action in ['OUT', 'ADJ']:
            product.quantity -= quantity_changed # Adjusted down or sold
            
        product.save()
        
        # History track karo
        InventoryLog.objects.create(
            product=product, user=request.user, action=action,
            quantity_changed=quantity_changed if action == 'IN' else -quantity_changed,
            previous_quantity=previous_quantity, new_quantity=product.quantity,
            notes=notes
        )
        
        response = HttpResponse()
        response['HX-Trigger'] = 'inventoryRefresh'
        return response
        
    return render(request, 'inventory/partials/stock_modal.html', {'product': product})

# --- PRODUCT HISTORY ---
@login_required
def product_history(request, product_id):
    product = get_object_or_404(Product, id=product_id, company=request.user.company)
    logs = product.stock_history.all().order_by('-timestamp')
    return render(request, 'inventory/partials/history_modal.html', {'product': product, 'logs': logs})



# inventory/views.py mein upar imports mein ye add kar lena:
from .models import Vendor, PurchaseRecord
from .forms import VendorForm, PurchaseForm
from accounts.decorators import role_required # Tere banaye hue custom permissions

# ==========================================
# VENDOR & PURCHASE VIEWS
# ==========================================

@login_required
@role_required(['admin', 'owner', 'ceo', 'manager'])
def vendor_list(request):
    company = request.user.company
    vendors = Vendor.objects.filter(company=company).order_by('-created_at')
    recent_purchases = PurchaseRecord.objects.filter(company=company).order_by('-purchase_date')[:10]
    
    base_template = 'shared/base_partial.html' if request.headers.get('HX-Request') else 'shared/base.html'
    
    return render(request, 'inventory/vendor_dashboard.html', {
        'vendors': vendors,
        'recent_purchases': recent_purchases,
        'base_template': base_template,
        'page_title': 'Vendors & Purchases'
    })

@login_required
@role_required(['admin', 'owner', 'ceo', 'manager'])
def add_vendor(request):
    if request.method == 'POST':
        form = VendorForm(request.POST)
        if form.is_valid():
            vendor = form.save(commit=False)
            vendor.company = request.user.company
            vendor.save()
            return HttpResponse(status=204, headers={'HX-Trigger': 'vendorRefresh'})
    else:
        form = VendorForm()
    
    return render(request, 'inventory/partials/modal_form.html', {'form': form, 'title': 'Add New Vendor', 'url': reverse('inventory:add_vendor')})

@login_required
@role_required(['admin', 'owner', 'ceo', 'manager'])
def add_purchase(request):
    if request.method == 'POST':
        form = PurchaseForm(request.POST, company=request.user.company)
        if form.is_valid():
            purchase = form.save(commit=False)
            purchase.company = request.user.company
            purchase.save() # Isse total_cost auto calculate ho jayega
            
            # MAGICAL PART: Auto-update Product Stock & Create Log
            product = purchase.product
            previous_qty = product.quantity
            
            product.quantity += purchase.quantity # Stock bada diya
            product.purchase_price = purchase.unit_cost # Naya rate update kar diya
            product.save()
            
            # History track kar li
            InventoryLog.objects.create(
                product=product, user=request.user, action='IN',
                quantity_changed=purchase.quantity,
                previous_quantity=previous_qty, new_quantity=product.quantity,
                notes=f"Purchased from {purchase.vendor.name}. Bill Ref: {purchase.reference_number}"
            )
            
            return HttpResponse(status=204, headers={'HX-Trigger': 'vendorRefresh'})
    else:
        form = PurchaseForm(company=request.user.company)
        
    return render(request, 'inventory/partials/modal_form.html', {'form': form, 'title': 'Record Purchase (Stock In)', 'url': reverse('inventory:add_purchase')})