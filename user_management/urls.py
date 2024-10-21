from django.urls import path
from .views import remove_chatbot_relation

urlpatterns = [
    # Other admin URLs
    path('user/<int:chatbot_id>/remove_relation/<int:user_id>/', remove_chatbot_relation, name='chatbot_chatbot_remove_relation'),
]
