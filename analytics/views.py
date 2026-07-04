import json
import traceback
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q, F, Max, Avg
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta
from collections import Counter
from itertools import combinations
from django.contrib.auth import get_user_model

from inventory.models import Product, InventoryLog
from billing.models import Invoice, Client
from taskms.models import Task
from accounts.decorators import role_required
from .bot_engine import TrueAIEngine 
from .models import ChatSession, ChatMessage
from django.db.models.functions import Coalesce

User = get_user_model()

@login_required
@role_required(['admin', 'owner', 'ceo', 'manager'])
def ai_dashboard(request):
    company = request.user.company
    today = timezone.now().date()
    last_month = today - timedelta(days=30)
    ninety_days_ago = today - timedelta(days=90) # Naya variable for Forecasting

    # 1. Base Data
    products = Product.objects.filter(company=company)
    
    # --- 2. ABC ANALYSIS (Pareto Optimization) ---
    inventory_items = products.annotate(
        total_item_value=F('quantity') * F('unit_price')
    ).order_by('-total_item_value')

    total_inventory_value = sum(item.total_item_value for item in inventory_items) or Decimal('1')
    abc_report = {'A': [], 'B': [], 'C': []}
    cumulative_value = Decimal('0.00')

    for item in inventory_items:
        cumulative_value += item.total_item_value
        percent = (cumulative_value / total_inventory_value) * 100
        if percent <= 70: abc_report['A'].append(item)
        elif percent <= 90: abc_report['B'].append(item)
        else: abc_report['C'].append(item)

    # --- 3. FAST MOVING ITEMS (Time-Series) ---
    fast_moving = InventoryLog.objects.filter(
        product__company=company, action='OUT', timestamp__date__gte=last_month
    ).values('product__name').annotate(
        total_sold=Sum(F('quantity_changed') * -1)
    ).order_by('-total_sold')[:5]

    # --- 4. MARKET BASKET ANALYSIS (Apriori Algorithm) ---
    target_invoices = Invoice.objects.filter(company=company, status__in=['paid', 'sent']).select_related('client')
    pairs_counter = Counter()

    for inv in target_invoices:
        client_name = inv.client.name.strip().lower()
        items_in_inv = []
        for item in inv.items.all():
            name = item.product.name if item.product else item.description
            if name:
                name_cleaned = name.strip()
                if name_cleaned.lower() != client_name:
                    items_in_inv.append(name_cleaned)
        
        items_in_inv = list(set(items_in_inv))
        if len(items_in_inv) > 1:
            pairs = combinations(sorted(items_in_inv), 2)
            pairs_counter.update(pairs)

    recommended_bundles = []
    for (name1, name2), count in pairs_counter.most_common(3):
        recommended_bundles.append({'p1': name1, 'p2': name2, 'count': count})

    # --- 5. CUSTOMER CLUSTERING (RFM Analysis) ---
    rfm_data = Client.objects.filter(company=company, invoices__status__in=['paid', 'sent']).annotate(
        last_purchase=Max('invoices__date'),
        total_orders=Count('invoices', distinct=True),
        total_spent=Coalesce(Sum('invoices__total_amount'), Decimal('0.00'))
    ).distinct()

    customer_clusters = {'champions': [], 'at_risk': [], 'newbies': []}
    for client in rfm_data:
        spent = client.total_spent
        orders = client.total_orders
        last_date = client.last_purchase
        if not last_date: continue

        if last_date >= last_month and orders > 1 and spent >= 1000:
            customer_clusters['champions'].append(client)
        elif last_date < last_month and spent >= 500:
            customer_clusters['at_risk'].append(client) 
        elif last_date >= last_month and orders == 1:
            customer_clusters['newbies'].append(client)

    # --- 6. ANOMALY DETECTION (Z-Score logic) ---
    recent_out_logs = InventoryLog.objects.filter(product__company=company, action='OUT', timestamp__date__gte=today - timedelta(days=7))
    anomalies = []
    for log in recent_out_logs:
        avg_out = InventoryLog.objects.filter(product=log.product, action='OUT').aggregate(Avg('quantity_changed'))['quantity_changed__avg'] or 0
        actual_qty = abs(log.quantity_changed)
        avg_out = abs(avg_out)
        
        if avg_out > 0 and actual_qty >= (avg_out * 3) and actual_qty > 10:
            anomalies.append({
                'product': log.product.name, 'qty': actual_qty, 'avg': round(avg_out, 1), 'date': log.timestamp
            })
    anomalies = anomalies[:4]

    # --- 7. BASIC METRICS ---
    low_stock_items = products.filter(quantity__lte=F('low_stock_threshold')).order_by('quantity')[:5]
    top_clients = Client.objects.filter(company=company).annotate(
        total_spent=Coalesce(Sum('invoices__total_amount', filter=Q(invoices__status='paid')), Decimal('0.00'))
    ).order_by('-total_spent')[:4]

    # =========================================================
    # 🔥 NAYA FEATURE 1: PREDICTIVE DEMAND FORECASTING
    # =========================================================
    # Pichle 90 dino ki sales nikal kar agle mahine ka demand predict karna
    sales_90_days = InventoryLog.objects.filter(
        product__company=company, action='OUT', timestamp__date__gte=ninety_days_ago
    ).values('product__name', 'product__quantity').annotate(
        total_sold=Sum(F('quantity_changed') * -1)
    )

    demand_forecasts = []
    for item in sales_90_days:
        avg_monthly_demand = item['total_sold'] / 3 # 3 mahine ka average
        recommended_stock = int(avg_monthly_demand * 1.5) # 1.5x Safety Stock
        current_stock = item['product__quantity']

        if current_stock < recommended_stock:
            demand_forecasts.append({
                'name': item['product__name'],
                'current': current_stock,
                'demand': int(avg_monthly_demand),
                'suggested_reorder': recommended_stock - current_stock
            })
    demand_forecasts = sorted(demand_forecasts, key=lambda x: x['suggested_reorder'], reverse=True)[:4]

    # =========================================================
    # 🔥 NAYA FEATURE 2: SMART TASK ALLOCATION (Load Balancing)
    # =========================================================
    # Check karna kis staff ke paas sabse kam active tasks hain
    staff_workload = Task.objects.filter(company=company).values(
        'assigned_to__first_name', 'assigned_to__last_name'
    ).annotate(
        active_tasks=Count('id', filter=Q(status__in=['pending', 'in_progress'])),
        completed_tasks=Count('id', filter=Q(status='completed'))
    ).order_by('active_tasks')

    # Filter out unassigned and format
    clean_workload = []
    for staff in staff_workload:
        if staff['assigned_to__first_name']:
            name = f"{staff['assigned_to__first_name']} {staff['assigned_to__last_name'] or ''}".strip()
            clean_workload.append({
                'name': name,
                'active': staff['active_tasks'],
                'completed': staff['completed_tasks']
            })
    
    optimal_assignee = clean_workload[0] if clean_workload else None

    return render(request, 'analytics/ai_dashboard.html', {
        'page_title': 'AI Decision Support',
        'abc_report': abc_report,
        'fast_moving': fast_moving,
        'low_stock_items': low_stock_items,
        'top_clients': top_clients,
        'bundles': recommended_bundles,
        'customer_clusters': customer_clusters,
        'anomalies': anomalies,
        'demand_forecasts': demand_forecasts, 
        'staff_workload': clean_workload[:4], # 
        'optimal_assignee': optimal_assignee 
    })

@login_required
def ai_chatbot_response(request):
    """Chatbot Endpoint with Full Access"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_msg = data.get('message', '').strip()
            if not user_msg:
                return JsonResponse({'error': 'Empty message'}, status=400)

            session, _ = ChatSession.objects.get_or_create(user=request.user, company=request.user.company)
            ChatMessage.objects.create(session=session, sender='user', text=user_msg)

            engine = TrueAIEngine(company=request.user.company, user=request.user)
            bot_reply = engine.generate_response(user_msg)
            
            ChatMessage.objects.create(session=session, sender='bot', text=bot_reply)
            return JsonResponse({'reply': bot_reply})
            
        except Exception as e:
            print("\n🚨 ASLI ERROR YAHAN HAI 🚨")
            print(traceback.format_exc())
            return JsonResponse({'reply': "Bhai, backend mein kuch phata hai. Check Terminal."})

    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def get_chat_history(request):
    """Fetches the previous chat history for the user upon page load"""
    try:
        session = ChatSession.objects.filter(user=request.user, company=request.user.company).first()
        if not session:
            return JsonResponse({'messages': []})

        history_msgs = session.messages.all().order_by('timestamp')
        data = [{'sender': m.sender, 'text': m.text} for m in history_msgs]
        return JsonResponse({'messages': data})
    except Exception as e:
        return JsonResponse({'error': 'Could not load history'}, status=500)