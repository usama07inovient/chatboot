from django.urls import path
from . import views

urlpatterns = [
    path('send_message/', views.handle_message, name='send_message'),  # AJAX handler
    path('chat/<str:platform_key>/', views.chatbot_view, name='chatbot'),
    # path('form/<str:platform_key>/', views.form_view, name='form'),
    path('form/<str:platform_key>/', views.form_detail_view, name='form-detail'),
    path('api/evaluate-interest/', views.evaluate_interest_api, name='evaluate_interest_api'),
    path('api/add-email/', views.HubSpotEmailView.as_view(), name='add_email'),
]
