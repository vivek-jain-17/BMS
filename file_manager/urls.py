from django.urls import path
from . import views

app_name = 'file_manager'

urlpatterns = [
    path('', views.manager_home, name='dashboard'),
    path('folder/<int:folder_id>/', views.folder_detail, name='folder_detail'),
    path('create-folder/', views.create_folder, name='create_folder'),
    path('upload/', views.upload_file, name='upload_file'),
]