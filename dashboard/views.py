import json
from datetime import timedelta
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, F, Q
from django.db.models.functions import Coalesce
from django.utils import timezone
from decimal import Decimal

from accounts.models import User
from taskms.models import Task
from inventory.models import Product
from billing.models import Invoice

@login_required
def home(request):
    company = request.user.company
    if not company:
        return render(request, 'dashboard/no_company.html', {'base_template': 'shared/base.html'})

    # --- 1. BASIC STATS ---
    total_staff = User.objects.filter(company=company).count()
    pending_tasks = Task.objects.filter(company=company, status__in=['pending', 'in_progress']).count()
    recent_tasks = Task.objects.filter(company=company).order_by('-created_at')[:5]
    
    products = Product.objects.filter(company=company)
    total_products = products.count()
    low_stock_products = [p for p in products if p.is_low_stock]
    
    # --- 2. FINANCIAL STATS (NAYA FEATURE) ---
    invoices = Invoice.objects.filter(company=company)
    # Total aayi hui rakam (Paid)
    total_revenue = invoices.filter(status='paid').aggregate(
        total=Coalesce(Sum('total_amount'), Decimal('0.00'))
    )['total']
    # Total baaki rakam (Udhaari / Sent / Overdue)
    outstanding_amount = invoices.filter(status__in=['sent', 'overdue']).aggregate(
        total=Coalesce(Sum('total_amount'), Decimal('0.00'))
    )['total']

    # --- 3. CHART DATA: MONTHLY REVENUE (Paid vs Expected) ---
    six_months_ago = timezone.now().date() - timedelta(days=180)
    recent_invoices = invoices.filter(date__gte=six_months_ago).order_by('date')
    
    months_dict = {}
    for inv in recent_invoices:
        m_str = inv.date.strftime("%b %Y")
        if m_str not in months_dict:
            months_dict[m_str] = {'paid': 0.0, 'expected': 0.0}
            
        if inv.status == 'paid':
            months_dict[m_str]['paid'] += float(inv.total_amount)
        elif inv.status in ['sent', 'overdue']:
            months_dict[m_str]['expected'] += float(inv.total_amount)

    months_list = list(months_dict.keys())
    paid_list = [v['paid'] for v in months_dict.values()]
    expected_list = [v['expected'] for v in months_dict.values()]

    if not months_list:
        months_list = ['No Data']
        paid_list = [0]
        expected_list = [0]

    # --- 4. CHART DATA: INVENTORY BY CATEGORY (Top 5 Only) ---
    category_data = products.values('category__name').annotate(
        total_value=Coalesce(Sum(F('quantity') * F('unit_price')), Decimal('0.00'))
    ).order_by('-total_value')[:5] # Sirf top 5 warna pie chart ganda dikhega
    
    cat_labels = [data['category__name'] or 'Uncategorized' for data in category_data]
    cat_values = [float(data['total_value']) for data in category_data]

    if not cat_labels:
        cat_labels = ['Empty']
        cat_values = [1]

    top_products = Product.objects.filter(company=company).order_by('-unit_price')[:4]

    context = {
        'page_title': 'Dashboard Overview',
        'total_staff': total_staff,
        'pending_tasks': pending_tasks,
        'total_products': total_products,
        'low_stock_count': len(low_stock_products),
        'recent_tasks': recent_tasks,
        'low_stock_items': low_stock_products[:5],
        
        # New Financials
        'total_revenue': total_revenue,
        'outstanding_amount': outstanding_amount,
        
        # Charts Data
        'chart_months': json.dumps(months_list),
        'chart_paid': json.dumps(paid_list),
        'chart_expected': json.dumps(expected_list),
        'chart_cat_labels': json.dumps(cat_labels),
        'chart_cat_values': json.dumps(cat_values),

        'top_products': top_products
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