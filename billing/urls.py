from django.urls import path
from . import views

app_name = 'billing'

urlpatterns = [
    path('', views.invoice_list, name='invoice_list'),
    path('create/', views.create_invoice, name='create_invoice'),
    path('clients/', views.client_list, name='client_list'),
    path('clients/add/', views.add_client, name='add_client'),
    path('clients/<int:client_id>/', views.client_profile, name='client_profile'),
    path('invoice/<int:invoice_id>/pdf/', views.generate_invoice_pdf, name='invoice_pdf'),
]