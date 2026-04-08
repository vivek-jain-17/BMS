from django import forms
from .models import Category, Product

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm'})

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'sku', 'category', 'description', 'quantity', 'low_stock_threshold', 'unit_price']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        
        if company:
            self.fields['category'].queryset = Category.objects.filter(company=company)
            self.fields['category'].empty_label = "Select Category"
            
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm'})




# inventory/forms.py
from django import forms
from .models import Category, Product, Vendor, PurchaseRecord

# ... (Tere CategoryForm aur ProductForm yahan rahenge) ...

class VendorForm(forms.ModelForm):
    class Meta:
        model = Vendor
        fields = ['name', 'contact_person', 'phone', 'email', 'address']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'w-full p-2 border rounded-lg mb-4'})
        self.fields['address'].widget.attrs.update({'rows': 3})

class PurchaseForm(forms.ModelForm):
    class Meta:
        model = PurchaseRecord
        fields = ['vendor', 'product', 'quantity', 'unit_cost', 'reference_number']

    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company')
        super().__init__(*args, **kwargs)
        # Dropdown mein sirf apni company ke vendors aur products dikhao
        self.fields['vendor'].queryset = Vendor.objects.filter(company=company)
        self.fields['product'].queryset = Product.objects.filter(company=company)
        
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'w-full p-2 border rounded-lg mb-4'})