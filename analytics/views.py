import json
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta

from inventory.models import Product
from billing.models import Invoice, Client
from taskms.models import Task
from accounts.decorators import role_required
from .bot_engine import TrueAIEngine 
from .models import ChatSession, ChatMessage
import traceback

# --- AI INSIGHTS DASHBOARD ---
@login_required
@role_required(['admin', 'owner', 'ceo', 'manager'])
def ai_dashboard(request):
    company = request.user.company
    today = timezone.now().date()

    products = Product.objects.filter(company=company)
    stock_predictions = []
    
    for product in products:
        daily_burn_rate = 1.5 # Example logic, replace with actual sales calculation later
        days_left = int(product.quantity / daily_burn_rate) if daily_burn_rate > 0 else 999
        if days_left <= 15:
            stock_predictions.append({
                'name': product.name, 'current_stock': product.quantity,
                'days_left': days_left, 'status': 'Critical' if days_left <= 5 else 'Warning'
            })

    overdue_tasks = Task.objects.filter(company=company, due_date__lt=today).exclude(status='completed').values('assigned_to__first_name').annotate(delayed_count=Count('id')).order_by('-delayed_count')[:5]
    
    top_clients = Client.objects.filter(company=company).annotate(total_spent=Sum('invoices__total_amount', filter=Q(invoices__status='paid'))).order_by('-total_spent')[:3]

    base_template = 'shared/base_partial.html' if request.headers.get('HX-Request') else 'shared/base.html'

    context = {
        'page_title': 'AI Decision Support',
        'base_template': base_template,
        'stock_predictions': sorted(stock_predictions, key=lambda x: x['days_left']),
        'overdue_staff': overdue_tasks,
        'top_clients': top_clients,
    }
    return render(request, 'analytics/ai_dashboard.html', context)

# --- TRUE AI CHATBOT ROUTE ---
@login_required
def ai_chatbot_response(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_msg = data.get('message', '').strip()
            if not user_msg: return JsonResponse({'error': 'Empty message'}, status=400)

            session, _ = ChatSession.objects.get_or_create(user=request.user, company=request.user.company)
            ChatMessage.objects.create(session=session, sender='user', text=user_msg)

            engine = TrueAIEngine(company=request.user.company, user=request.user)
            bot_reply = engine.generate_response(user_msg)
            
            ChatMessage.objects.create(session=session, sender='bot', text=bot_reply)
            return JsonResponse({'reply': bot_reply})
            
        except Exception as e:
            print("\n🚨 ASLI ERROR YAHAN HAI 🚨")
            print(traceback.format_exc())
            print("🚨=========================🚨\n")
            
            return JsonResponse({'reply': "System error. Could not reach the AI."})

    return JsonResponse({'error': 'Invalid request'}, status=400)