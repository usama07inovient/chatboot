# user_management/models.py

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

class User(AbstractUser):
    platform_name = models.CharField(max_length=255, blank=True, null=True)
    profile_pic = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    logo = models.ImageField(upload_to='logos/', blank=True, null=True)
    website_url = models.URLField(max_length=200, blank=True)
    date_of_subscription = models.DateField(default=timezone.now)

    def __str__(self):
        return self.username

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
