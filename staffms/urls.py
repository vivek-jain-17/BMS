# staffms/urls.py
from django.urls import path
from . import views

app_name = 'staffms'

urlpatterns = [
    path('', views.staff_list, name='staff_list'),
    path('add/', views.add_staff, name='add_staff'),
    path('profile/<uuid:user_id>/', views.staff_profile, name='staff_profile'),
]