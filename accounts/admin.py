from django.contrib import admin
from .models import Company, User, Roles, Teams, UserRoles, UserTeams

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'subdomain', 'is_active', 'created_at')
    search_fields = ('name', 'subdomain')
    list_filter = ('is_active',)

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'company', 'is_staff', 'is_active')
    search_fields = ('email', 'first_name', 'last_name')
    list_filter = ('is_staff', 'is_active', 'company')
    readonly_fields = ('last_login', 'created_at', 'updated_at')

# Registering the rest of the models simply
admin.site.register(Roles)
admin.site.register(Teams)
admin.site.register(UserRoles)
admin.site.register(UserTeams)