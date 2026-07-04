from django.contrib import admin
from .models import Folder, Document

@admin.register(Folder)
class FolderAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'is_private', 'created_at')
    list_filter = ('is_private', 'company')
    search_fields = ('name', 'company__name')
    ordering = ('-created_at',)

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'folder', 'uploaded_by', 'get_extension', 'created_at')
    list_filter = ('company', 'created_at')
    search_fields = ('title', 'company__name', 'uploaded_by__email', 'uploaded_by__first_name')
    readonly_fields = ('file_size', 'created_at')
    ordering = ('-created_at',)

    # Custom column in Admin to show file extension
    def get_extension(self, obj):
        return obj.extension()
    get_extension.short_description = 'Ext'