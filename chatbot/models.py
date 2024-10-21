from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

# chatbot name, save user chatsession

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
import uuid
from data_pipeline.models import DataPipeline

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from user_management.models import User


# chatbot/models.py

from django.db import models
from user_management.models import User  # Assuming User is moved to user_management app
import uuid

class Chatbot(models.Model):
    # Change from ForeignKey to ManyToManyField to allow multiple users
    users = models.ManyToManyField(User, related_name='chatbots', blank=True)
    
    name = models.CharField(max_length=255, default='Virtual Assistant')
    logo = models.ImageField(upload_to='chatbot_logos/', blank=True, null=True)
    platform_key = models.CharField(max_length=255, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    save_user_chatsession = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.name}'

    class Meta:
        permissions = [
            ('create_own_chatbot', 'Can create own chatbots'),
            ('delete_own_chatbot', 'Can delete own chatbots'),
            ('update_own_chatbot', 'Can update own chatbots'),
            ('view_own_chatbot', 'Can view own chatbots'),
            ('activate_chatbot', 'Can activate/deactivate chatbots'),
            ('modify_chat_save_session', 'Can modify save chat session settings'),
        ]

    def regenerate_plateform_key(self):
        """Regenerate the API key for the chatbot."""
        self.platform_key = str(uuid.uuid4())
        self.save()

    def save(self, *args, **kwargs):
        """Override save to ensure API key is set on creation."""
        if not self.platform_key:
            self.regenerate_plateform_key()
        super().save(*args, **kwargs)


class ChatSession(models.Model):
    chatbot = models.ForeignKey(Chatbot, on_delete=models.CASCADE)  # Associate each chat session with a specific chatbot
    username = models.CharField(max_length=255)
    email = models.EmailField()
    started_at = models.DateTimeField(default=timezone.now)
    chat_history = models.JSONField(default=list)  # JSONField works with SQLite in Django 3.1+

    def __str__(self):
        return f'Chat with {self.username} on {self.chatbot.name}'

    def add_message(self, message):
        """
        Add a new message to the chat history.
        If there are more than 10 messages, remove the oldest.
        """
        self.chat_history.append(message)
        if len(self.chat_history) > 10:
            self.chat_history = self.chat_history[-10:]  # Keep only the last 10 messages
        self.save()

    def get_message_history(self):
        return self.chat_history


class Form(models.Model):
    chatbot = models.OneToOneField(Chatbot, related_name='form', on_delete=models.CASCADE)  # One-to-one with Chatbot
    title = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    whatsapp_link = models.CharField(max_length=255, blank=True, null=True)
    def __str__(self):
        return self.title


    class Meta:
        permissions = [
            ('add_own_form', 'Can add own forms'),
            ('update_own_form', 'Can update own forms'),
            ('delete_own_form', 'Can delete own forms'),
            ('view_own_form', 'Can view own forms')
        ]



class Question(models.Model):
    ANSWER_CHOICES = [
        ('yes', 'Yes'),
        ('no', 'No'),
    ]
    form = models.ForeignKey(Form, related_name='questions', on_delete=models.CASCADE)  # A form has many questions
    text = models.CharField(max_length=500)  # Question text
    answer = models.CharField(max_length=3, choices=ANSWER_CHOICES)

    def __str__(self):
        return self.text

    def is_correct(self, user_answer):
        """Check if the user's submitted answer is correct."""
        return self.answer == user_answer


# class Answer(models.Model):
#     ANSWER_CHOICES = [
#         ('yes', 'Yes'),
#         ('no', 'No'),
#     ]
#     answer = models.CharField(max_length=3, choices=ANSWER_CHOICES)  # Yes or No answer

#     def __str__(self):
#         return self.get_answer_display()
