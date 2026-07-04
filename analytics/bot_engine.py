from groq import Groq
from django.conf import settings
from django.db.models import Sum
from inventory.models import Product, InventoryLog
from billing.models import Invoice, Client
from taskms.models import Task

class TrueAIEngine:
    def __init__(self, company, user):
        self.company = company
        self.user = user
        self.client = Groq(api_key=settings.GROQ_API_KEY)

    def get_business_context(self):
        """Database se History samet sab kuch nikalna"""
        
        # 1. PRODUCT CATALOG (Full Details)
        products = Product.objects.filter(company=self.company)
        prod_list = [f"- {p.name}: {p.quantity} in stock (SKU: {p.sku}, Price: ₹{p.unit_price})" for p in products]
        inventory_context = "\n".join(prod_list) if prod_list else "No products found."

        # 2. INVENTORY HISTORY (Pichle 15 Logs)
        logs = InventoryLog.objects.filter(product__company=self.company).order_by('-timestamp')[:15]
        history_list = []
        for l in logs:
            user_name = l.user.first_name if l.user else "System"
            history_list.append(f"- {l.timestamp.strftime('%d %b, %H:%M')} | {l.product.name} | {l.get_action_display()} | Qty: {l.quantity_changed} | New Total: {l.new_quantity} | By: {user_name}")
        history_context = "\n".join(history_list) if history_list else "No recent history logs."

        # 3. TASK & STAFF DETAIL
        tasks = Task.objects.filter(company=self.company)
        task_list = []
        for t in tasks:
            assignee = t.assigned_to.first_name if t.assigned_to else "Unassigned"
            task_list.append(f"- [{t.status.upper()}] {t.title} assigned to {assignee}")
        tasks_context = "\n".join(task_list) if task_list else "No tasks found."

        # 4. REVENUE & CLIENTS
        total_rev = Invoice.objects.filter(company=self.company, status='paid').aggregate(Sum('total_amount'))['total_amount__sum'] or 0

        # FINAL CONTEXT
        context = f"""
        LIVE SYSTEM STATE FOR {self.company.name.upper()}:
        
        --- INVENTORY CATALOG ---
        {inventory_context}
        
        --- RECENT INVENTORY HISTORY (LOGS) ---
        {history_context}
        
        --- TASK MANAGEMENT ---
        {tasks_context}
        
        --- FINANCIALS ---
        Total Revenue: ₹{total_rev}
        """
        return context

    def generate_response(self, user_message):
        business_data = self.get_business_context()

        # 🔥 OPTIMIZED SYSTEM INSTRUCTIONS WITH GUARDRAILS 🔥
        system_instruction = f"""
        You are 'BMS PRO AI CORE', a strict and highly intelligent Business Management & ERP Assistant.
        You are talking to: {self.user.first_name} (The Boss/Manager).

        YOUR CORE DIRECTIVES & GUARDRAILS:
        1. BOUNDARY RESTRICTION: You MUST ONLY answer questions related to:
           - The provided 'LIVE SYSTEM STATE' (Inventory, Tasks, Logs, Revenue).
           - General business, management, finance, or corporate advice.
           If the user asks ANYTHING outside this scope (e.g., coding, general trivia, politics, jokes, recipe), you MUST politely decline and state that you are exclusively a Business Management AI.
        
        2. LANGUAGE MIRRORING: You MUST respond in the EXACT same language the user is asking the question in.
           - If they ask in pure English -> Reply in English.
           - If they ask in pure Hindi -> Reply in Hindi (Devanagari).
           - If they ask in Hinglish (Hindi written in English alphabet) -> Reply in Hinglish.
           - If they ask in Marathi, Gujarati, etc. -> Reply in that exact language.
        
        3. DATA UTILIZATION:
           - If asked "Who added stock?", search the 'RECENT INVENTORY HISTORY'.
           - Mention specific dates, times, and user names when looking at logs.
           - Never say you don't have details if the details are present in the provided DATA.

        Be concise, accurate, and professional.
        """

        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "system", "content": f"DATA:\n{business_data}"},
                    {"role": "user", "content": user_message},
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.1, # Temperature lowered to 0.1 for stricter adherence to guardrails
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            return f"Boss, Engine error: {str(e)}"