from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from accounts.models import User
from taskms.models import Task
from inventory.models import Product
import json
from django.db.models import Sum, F
from django.db.models.functions import TruncMonth

@login_required
def home(request):
    company = request.user.company
    if not company:
        return render(request, 'dashboard/no_company.html', {'base_template': 'shared/base.html'})

    # --- 1. BASIC STATS (Tere Purane wale) ---
    total_staff = User.objects.filter(company=company).count()
    pending_tasks = Task.objects.filter(company=company, status='pending').count()
    recent_tasks = Task.objects.filter(company=company).order_by('-created_at')[:5]
    
    products = Product.objects.filter(company=company)
    total_products = products.count()
    low_stock_products = [p for p in products if p.is_low_stock]
    
    # --- 2. CHART DATA: MONTHLY REVENUE (Bar Chart) ---
    # Invoices ko mahine ke hisaab se group karke unka total sum nikal rahe hain
    from billing.models import Invoice # Import yahan kar liya safety ke liye
    
    revenue_data = Invoice.objects.filter(company=company, status__in=['paid', 'sent']).annotate(
        month=TruncMonth('date')
    ).values('month').annotate(total=Sum('total_amount')).order_by('month')

    # Data ko list mein convert karna taaki JS samajh sake
    months_list = [data['month'].strftime("%b %Y") for data in revenue_data]
    revenue_list = [float(data['total']) for data in revenue_data]
    
    # Agar data khali hai (naye user ke liye), toh dummy list bhej do
    if not months_list:
        months_list = ['No Data Yet']
        revenue_list = [0]

    # --- 3. CHART DATA: INVENTORY BY CATEGORY (Pie Chart) ---
    # Har category ka (Quantity * Price) nikal ke total value
    category_data = products.values('category__name').annotate(
        total_value=Sum(F('quantity') * F('unit_price'))
    )
    
    cat_labels = [data['category__name'] or 'Uncategorized' for data in category_data]
    cat_values = [float(data['total_value'] or 0) for data in category_data]

    if not cat_labels:
        cat_labels = ['Empty']
        cat_values = [1] # Pie chart khali dikhane ke liye 1 de diya

    base_template = 'shared/base_partial.html' if request.headers.get('HX-Request') else 'shared/base.html'
    
    context = {
        'total_staff': total_staff,
        'pending_tasks': pending_tasks,
        'total_products': total_products,
        'low_stock_count': len(low_stock_products),
        'recent_tasks': recent_tasks,
        'low_stock_items': low_stock_products[:5],
        'base_template': base_template,
        'page_title': 'Dashboard Overview',
        
        # CHARTS DATA (JSON format mein taaki Javascript read kar sake)
        'chart_months': json.dumps(months_list),
        'chart_revenues': json.dumps(revenue_list),
        'chart_cat_labels': json.dumps(cat_labels),
        'chart_cat_values': json.dumps(cat_values),
    }
    
    return render(request, 'dashboard/home.html', context)
from django.http import HttpResponse
from django.urls import reverse
from accounts.models import Company # Company model import karna mat bhoolna

@login_required
def create_workspace(request):
    if request.method == 'POST':
        company_name = request.POST.get('company_name')
        subdomain = request.POST.get('subdomain')

        if company_name:
            try:
                # 1. Nayi company create karo
                new_company = Company.objects.create(
                    name=company_name, 
                    subdomain=subdomain
                )
                
                # 2. Current logged-in user ko is company ka admin/hissa bana do
                request.user.company = new_company
                request.user.save()

                # 3. HTMX Redirect: Page ko main dashboard pe bhej do
                response = HttpResponse()
                response['HX-Redirect'] = reverse('dashboard:home')
                return response
                
            except Exception as e:
                # Agar subdomain already taken ho ya koi error aaye
                return render(request, 'dashboard/partials/create_workspace_modal.html', {
                    'error': 'This subdomain is already taken or invalid.',
                    'name': company_name, 'subdomain': subdomain
                })

    return render(request, 'dashboard/partials/create_workspace_modal.html')