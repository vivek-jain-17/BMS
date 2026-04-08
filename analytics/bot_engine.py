from groq import Groq
from django.conf import settings
from django.db.models import Sum
from inventory.models import Product
from billing.models import Invoice
from taskms.models import Task

class TrueAIEngine:
    def __init__(self, company, user):
        self.company = company
        self.user = user
        # Groq Client Initialization
        self.client = Groq(api_key=settings.GROQ_API_KEY)

    def get_business_context(self):
        # 1. Revenue
        try:
            total_rev = Invoice.objects.filter(company=self.company, status='paid').aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        except Exception:
            total_rev = "Unavailable"

        # 2. Inventory (Total + Low Stock)
        try:
            total_products = Product.objects.filter(company=self.company).count()
            low_stock_items = Product.objects.filter(company=self.company, quantity__lte=10)
            low_stock_names = ", ".join([f"{p.name} (Qty: {p.quantity})" for p in low_stock_items[:5]])
            if not low_stock_names: 
                low_stock_names = "None. Inventory is healthy."
        except Exception:
            total_products = "Unavailable"
            low_stock_names = "Unavailable"

        # 3. Tasks (Detailed for Staff)
        try:
            pending_tasks = Task.objects.filter(company=self.company).exclude(status='completed')
            total_pending = pending_tasks.count()
            
            task_details_list = []
            for t in pending_tasks[:10]: 
                assignee = t.assigned_to.first_name if t.assigned_to else "Unassigned"
                task_details_list.append(f"[{assignee}: {t.title} - {t.status}]")
            
            task_details_str = ", ".join(task_details_list) if task_details_list else "No pending tasks."
                
        except Exception:
            total_pending = "Unavailable"
            task_details_str = "Unavailable"

        # 4. Final Brain Context for LLM
        context = f"""
        LIVE BUSINESS DATA CONTEXT:
        - Company Name: {self.company.name}
        - Total Paid Revenue: ₹{total_rev}
        
        INVENTORY:
        - Total Products in Catalog: {total_products}
        - Low Stock Alert Items: {low_stock_names}
        
        TASKS (Current Status):
        - Total Pending Tasks: {total_pending}
        - Detailed Task List: {task_details_str}
        """
        return context

    def generate_response(self, user_message):
        business_data = self.get_business_context()

        system_instruction = f"""
        You are an intelligent, professional, and helpful Business Management Assistant for an ERP system called "BMS PRO". 
        You are talking to {self.user.first_name}, who is a manager/owner of '{self.company.name}'.
        
        Here is the LIVE DATA of their business right now:
        {business_data}

        INSTRUCTIONS:
        1. Answer questions based strictly on the live data provided above.
        2. Provide brief, actionable insights. Use bullet points or bold text for readability.
        3. DO NOT make up data. If data is missing or unavailable, say so politely.
        4. Match the user's language tone (Hinglish/English).
        """

        try:
            # Calling Groq API with Llama 3 8B model (Super fast and intelligent)
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": system_instruction,
                    },
                    {
                        "role": "user",
                        "content": user_message,
                    }
                ],
                model="llama3-8b-8192", # Llama 3 model on Groq
                temperature=0.3, # Low temperature to keep it factual and less hallucinated
            )
            return chat_completion.choices[0].message.content
            
        except Exception as e:
            print(f"Groq Error: {e}")
            return "Boss, Groq AI API key is missing, or the service is down right now."