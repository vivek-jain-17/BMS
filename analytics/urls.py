from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('insights/', views.ai_dashboard, name='ai_dashboard'),
    path('bot-reply/', views.ai_chatbot_response, name='ai_bot_reply'),
]