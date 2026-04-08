from django.contrib import admin
from .models import Task

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'assigned_to', 'status', 'priority', 'due_date')
    list_filter = ('status', 'priority', 'company')
    search_fields = ('title', 'description')