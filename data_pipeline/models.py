from django.db import models
from django.utils import timezone
import os
from django.core.exceptions import ValidationError
from django.conf import settings
import uuid
import shutil

def data_source_upload_to(instance, filename):
    """
    Custom function to generate a unique folder path based on the associated chatbot name and id.
    """
    folder = instance.data_pipeline.uuid
    folder_name = f'data_sources/{folder}'
    return os.path.join(folder_name, filename)

class DataPipeline(models.Model):
    name = models.CharField(max_length=255, default='Default Pipeline Name')
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)  # Unique UUID for folder name
    url = models.URLField(max_length=500, blank=True, null=True)
    status = models.CharField(max_length=50, choices=[('pending', 'Pending'), ('active', 'Active'), ('completed', 'Completed')], default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    chatbot = models.OneToOneField('chatbot.Chatbot', on_delete=models.SET_NULL, null=True, blank=True, related_name='data_pipeline')
    updated_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        if hasattr(self, 'chatbot') and self.chatbot:
            return f'{self.name} for {self.chatbot.name}'
        return f'{self.name}'
    
    def delete(self, *args, **kwargs):
        # Path to the directory to be deleted
        folder_path = os.path.join(settings.MEDIA_ROOT, 'data_sources', str(self.uuid))
        
        # Check if the directory exists and delete it
        if os.path.exists(folder_path) and os.path.isdir(folder_path):
            shutil.rmtree(folder_path)
        
        # Call the parent class's delete method to delete the DataPipeline instance
        super().delete(*args, **kwargs)

    class Meta:
        permissions = [
            ('add_own_pipeline', 'Can add own data pipelines'),
            ('update_own_pipeline', 'Can update own data pipelines'),
            ('delete_own_pipeline', 'Can delete own data pipelines'),
            ('view_own_pipeline', 'Can view own data pipelines')
        ]

def validate_file_size(file):
    """
    Validate the size of the uploaded file.
    """
    max_file_size = settings.MAX_FILE_SIZE_MB * 1024 * 1024  # Convert MB to bytes
    if file.size > max_file_size:
        raise ValidationError(f'The file size exceeds the {settings.MAX_FILE_SIZE_MB}MB limit. Please upload a smaller file.')

def validate_file_type(file):
    """
    Validate that the uploaded file has an allowed extension.
    """
    allowed_extensions = settings.ALLOWED_FILE_TYPES.split(',')  # Allowed file types
    ext = os.path.splitext(file.name)[1]  # Get the file extension
    if ext.lower() not in allowed_extensions:
        raise ValidationError(f'Unsupported file type. Allowed types are: {", ".join(allowed_extensions)}')
    
class DataSource(models.Model):
    data_pipeline = models.ForeignKey(DataPipeline, related_name='data_sources', on_delete=models.CASCADE, default=1)
    file = models.FileField(upload_to=data_source_upload_to, validators=[validate_file_size,validate_file_type])  # Add validator here
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'DataSource for {self.data_pipeline.name}'
