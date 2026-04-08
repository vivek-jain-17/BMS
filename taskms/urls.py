from django.urls import path
from . import views

app_name = 'taskms'

urlpatterns = [
    path('board/', views.task_board, name='task_board'),
    path('update-status/<int:task_id>/', views.update_task_status, name='update_status'),
    path('add/', views.add_task, name='add_task'),
    path('edit/<int:task_id>/', views.edit_task, name='edit_task'),
    path('delete/<int:task_id>/', views.delete_task, name='delete_task'),
]