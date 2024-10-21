from django.shortcuts import redirect
from django.contrib import messages
from chatbot.models import Chatbot
from user_management.models import User

# Custom view to remove the relationship between a user and a chatbot
def remove_chatbot_relation(request, chatbot_id, user_id):
    try:
        chatbot = Chatbot.objects.get(pk=chatbot_id)
        user = User.objects.get(pk=user_id)
        chatbot.users.remove(user)  # Remove the Many-to-Many relationship
        messages.success(request, "Chatbot has been removed from the user.")
    except Chatbot.DoesNotExist:
        messages.error(request, "Chatbot does not exist.")
    except User.DoesNotExist:
        messages.error(request, "User does not exist.")
    
    return redirect('admin:user_management_user_change', user_id)
