# staffms/forms.py
from django import forms
from accounts.models import User

class StaffCreationForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'phone_number', 'monthly_salary', 'joining_date']
        widgets = {
            'joining_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply Tailwind classes globally
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'mt-1 block w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm'
            })