from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Invoice, InvoiceItem, Client
from .forms import InvoiceForm, InvoiceItemFormSet

# 1. INVOICE LIST
@login_required
def invoice_list(request):
    if request.user.is_tier1 or request.user.is_manager_plus:
        invoices = Invoice.objects.filter(company=request.user.company).order_by('-date')
    else:
        invoices = Invoice.objects.filter(company=request.user.company, created_by=request.user)
    
    # HTMX Dynamic Base
    base_template = 'shared/base_partial.html' if request.headers.get('HX-Request') else 'shared/base.html'
    
    context = {
        'invoices': invoices,
        'base_template': base_template,
        'page_title': 'Invoices & Billing'
    }
    return render(request, 'billing/invoice_list.html', context)

# 2. CREATE INVOICE
@login_required
def create_invoice(request):
    company = request.user.company
    
    if request.method == 'POST':
        form = InvoiceForm(request.POST, company=company)
        formset = InvoiceItemFormSet(request.POST, form_kwargs={'company': company})
        
        if form.is_valid() and formset.is_valid():
            # Invoice Save karo (Draft)
            invoice = form.save(commit=False)
            invoice.company = company
            invoice.save()
            
            # Formset Save karo (Line Items)
            formset.instance = invoice
            items = formset.save(commit=False)
            
            # Calculations
            subtotal = 0
            for item in items:
                item.amount = item.quantity * item.rate
                subtotal += item.amount
                item.save()
                
            # Handle deleted items from formset
            for obj in formset.deleted_objects:
                obj.delete()
                
            # Final Totals
            invoice.subtotal = subtotal
            invoice.tax_amount = (subtotal * invoice.tax_percentage) / 100
            invoice.total_amount = subtotal + invoice.tax_amount - invoice.discount_amount
            invoice.save()
            
            # MAGIC: Agar invoice send ya paid ho gaya hai, toh inventory deduct karo
            if invoice.status in ['sent', 'paid']:
                invoice.deduct_inventory(request.user)
                
            messages.success(request, 'Invoice created successfully!')
            return redirect('billing:invoice_list')
    else:
        # Naya Invoice number generate karo (Example logic)
        last_invoice = Invoice.objects.filter(company=company).order_by('id').last()
        next_num = f"INV-{last_invoice.id + 1:04d}" if last_invoice else "INV-0001"
        
        form = InvoiceForm(company=company, initial={'invoice_number': next_num})
        formset = InvoiceItemFormSet(form_kwargs={'company': company})
        
    base_template = 'shared/base_partial.html' if request.headers.get('HX-Request') else 'shared/base.html'
    
    context = {
        'form': form,
        'formset': formset,
        'base_template': base_template,
        'page_title': 'Create New Invoice'
    }
    return render(request, 'billing/create_invoice.html', context)



# billing/views.py mein ye naye functions add karo
from django.http import HttpResponse
from django.urls import reverse
from .forms import ClientForm
from django.db.models import Sum

# --- 1. CLIENT LIST (CRM Dashboard) ---
@login_required
def client_list(request):
    clients = Client.objects.filter(company=request.user.company).order_by('-created_at')
    base_template = 'shared/base_partial.html' if request.headers.get('HX-Request') else 'shared/base.html'
    
    context = {
        'clients': clients,
        'base_template': base_template,
        'page_title': 'Clients & CRM'
    }
    return render(request, 'billing/client_list.html', context)

# --- 2. ADD CLIENT (HTMX Modal) ---
@login_required
def add_client(request):
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            client = form.save(commit=False)
            client.company = request.user.company
            client.save()
            
            # Modal band karke client list refresh karo
            response = HttpResponse()
            response['HX-Trigger'] = 'clientRefresh'
            return response
    else:
        form = ClientForm()
        
    return render(request, 'billing/partials/client_modal.html', {
        'form': form, 
        'title': 'Add New Client', 
        'url': reverse('billing:add_client')
    })

# --- 3. CLIENT PROFILE (History & Ledger) ---
@login_required
def client_profile(request, client_id):
    client = get_object_or_404(Client, id=client_id, company=request.user.company)
    invoices = client.invoices.all().order_by('-date')
    
    # Financial calculations
    total_billed = invoices.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    paid_invoices = invoices.filter(status='paid').aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    outstanding = total_billed - paid_invoices

    base_template = 'shared/base_partial.html' if request.headers.get('HX-Request') else 'shared/base.html'
    
    context = {
        'client': client,
        'invoices': invoices,
        'total_billed': total_billed,
        'outstanding': outstanding,
        'base_template': base_template,
        'page_title': f"{client.name} - Profile"
    }
    return render(request, 'billing/client_profile.html', context)



from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
# Apne models import section mein make sure ye hai: 
# from .models import Invoice

@login_required
def generate_invoice_pdf(request, invoice_id):
    # Invoice fetch karo security ke sath (sirf apni company ka)
    invoice = get_object_or_404(Invoice, id=invoice_id, company=request.user.company)
    
    # Template aur data
    template_path = 'billing/pdf/invoice_pdf.html'
    context = {
        'invoice': invoice,
        'company': request.user.company,
        'client': invoice.client,
        'items': invoice.items.all()
    }
    
    # PDF response setup
    response = HttpResponse(content_type='application/pdf')
    # Download karwana hai toh 'attachment', browser mein dikhana hai toh 'inline'
    response['Content-Disposition'] = f'attachment; filename="Invoice_{invoice.invoice_number}.pdf"'
    
    # HTML render karke PDF banao
    template = get_template(template_path)
    html = template.render(context)
    
    # Create PDF
    pisa_status = pisa.CreatePDF(html, dest=response)
    
    if pisa_status.err:
        return HttpResponse('We had some errors building the PDF.')
    
    return response