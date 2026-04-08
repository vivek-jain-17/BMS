from django import forms
from django.forms import inlineformset_factory
from .models import Invoice, InvoiceItem, Client
from inventory.models import Product

class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['client', 'invoice_number', 'date', 'due_date', 'status', 'tax_percentage', 'discount_amount']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'due_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        
        if company:
            self.fields['client'].queryset = Client.objects.filter(company=company)
            
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm'})


class InvoiceItemForm(forms.ModelForm):
    class Meta:
        model = InvoiceItem
        fields = ['product', 'description', 'quantity', 'rate']

    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        
        if company:
            self.fields['product'].queryset = Product.objects.filter(company=company)
            
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'mt-1 block w-full px-2 py-1.5 border border-gray-300 rounded-md text-sm'})

# Formset banate hain taaki ek invoice mein multiple items add kar sakein
InvoiceItemFormSet = inlineformset_factory(
    Invoice, InvoiceItem, form=InvoiceItemForm,
    extra=1, can_delete=True
)


# billing/forms.py mein ye form add karo
from .models import Client # Client import karna mat bhoolna

class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['name', 'email', 'phone', 'address', 'tax_number']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm'
            })