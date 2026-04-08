from django.db import models
from django.conf import settings
import os

class Folder(models.Model):
    company = models.ForeignKey('accounts.Company', on_delete=models.CASCADE, related_name='folders')
    name = models.CharField(max_length=100)
    # RBAC: Kya ye folder sirf Tier 1 dekh sakta hai? (e.g., Payroll, Finance)
    is_private = models.BooleanField(default=False) 
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.company.name})"

class Document(models.Model):
    company = models.ForeignKey('accounts.Company', on_delete=models.CASCADE, related_name='documents')
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE, related_name='files', null=True, blank=True)
    
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='company_docs/%Y/%m/%d/')
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    
    # Links (Optional: File kisi task ya client se judi ho sakti hai)
    related_client = models.ForeignKey('billing.Client', on_delete=models.SET_NULL, null=True, blank=True)
    related_task = models.ForeignKey('taskms.Task', on_delete=models.SET_NULL, null=True, blank=True)
    
    file_size = models.BigIntegerField(null=True, blank=True) # Bytes mein
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    def extension(self):
        name, extension = os.path.splitext(self.file.name)
        return extension.lower()