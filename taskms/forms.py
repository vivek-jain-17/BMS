from django import forms
from .models import Task
from accounts.models import User

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'assigned_to', 'priority', 'due_date']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        # Company ID nikal rahe hain kwargs se taaki staff filter kar sakein
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        
        if company:
            # Dropdown mein sirf apni company ke log dikhenge
            self.fields['assigned_to'].queryset = User.objects.filter(company=company)
            self.fields['assigned_to'].empty_label = "Unassigned"
            
        # Tailwind classes globally apply karne ke liye
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm'
            })