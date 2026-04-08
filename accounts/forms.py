# accounts/forms.py
from django import forms
from .models import User, Company

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            'first_name', 'middle_name', 'last_name', 
            'phone_number', 'phone_number2',
            'flat_number', 'building_name', 
            'street_name', 'city', 'state'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Automatically add Tailwind classes to all input fields
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'mt-1 block w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 text-sm'
            })



class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['name', 'subdomain']
        help_texts = {
            'subdomain': 'Choose a unique URL prefix for your business (e.g., "acme" for acme.bms.com). You can leave this blank for now.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'mt-1 block w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 text-sm'
            })