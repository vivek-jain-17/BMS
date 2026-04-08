from django import forms
from .models import Folder, Document

class FolderForm(forms.ModelForm):
    class Meta:
        model = Folder
        fields = ['name', 'is_private']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'w-full p-2 border rounded-lg mb-4'})

class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['title', 'folder', 'file', 'related_client', 'related_task']

    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company')
        super().__init__(*args, **kwargs)
        
        # Sirf apni company ke folders/tasks dikhao dropdown mein
        self.fields['folder'].queryset = Folder.objects.filter(company=company)
        # related_client aur related_task ke queryset bhi filter kar sakte ho same way
        
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'w-full p-2 border rounded-lg mb-4'})