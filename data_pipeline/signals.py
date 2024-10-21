from django.db.models.signals import post_save, post_delete, pre_save, pre_delete
from django.dispatch import receiver
from django.db import transaction
from threading import local
from .models import DataSource, DataPipeline
from django.utils import timezone
from .tasks import rag_update,test_rag_update
from celery.result import AsyncResult

# Thread-local storage for tracking added, updated, and deleted files
_thread_locals = local()

# Initialize thread-local variables if they do not exist
def init_file_changes():
    if not hasattr(_thread_locals, 'added_files'):
        _thread_locals.added_files = []
    if not hasattr(_thread_locals, 'deleted_files'):
        _thread_locals.deleted_files = []
    if not hasattr(_thread_locals, 'updated_files'):
        _thread_locals.updated_files = []
    if not hasattr(_thread_locals, 'pipeline_url_changes'):
        _thread_locals.pipeline_url_changes = None
    if not hasattr(_thread_locals, 'registered_for_commit'):
        _thread_locals.registered_for_commit = False  # Flag to avoid multiple registrations
    if not hasattr(_thread_locals, 'is_pipeline_deleting'):
        _thread_locals.is_pipeline_deleting = False  # Flag for pipeline deletion

def process_changes():
    added_files = getattr(_thread_locals, 'added_files', [])
    deleted_files = getattr(_thread_locals, 'deleted_files', [])
    updated_files = getattr(_thread_locals, 'updated_files', [])
    pipeline_url_changes = getattr(_thread_locals, 'pipeline_url_changes', None)
    pipeline_instance = getattr(_thread_locals, 'pipeline_instance', None)
    url_data_pipeline_uuid=None

    print("Processing Changes")
    print(f"Added Files: {[(f.file.name, f.data_pipeline.name) for f in added_files]}")
    print(f"Deleted Files: {[(f.file.name, f.data_pipeline.name) for f in deleted_files]}")
    print(f"Updated Files: {[(f.file.name, f.data_pipeline.name) for f in updated_files]}")

    if pipeline_url_changes:
        old_url, new_url = pipeline_url_changes
        print(f"Pipeline URL Changed from {old_url} to {new_url}")

    data_pipelines = set(instance.data_pipeline for instance in added_files + deleted_files + updated_files)
    if pipeline_instance:
        url_data_pipeline_uuid=pipeline_instance.uuid
        data_pipelines.add(pipeline_instance)

    for pipeline in data_pipelines:
        pipeline.status = 'pending'
        pipeline.updated_at = timezone.now()
        pipeline.save()

    added_files_serialized = [(f.file.name, f.data_pipeline.uuid) for f in added_files]
    updated_files_serialized = [(f.file.name, f.data_pipeline.uuid) for f in updated_files]
    deleted_files_serialized = [(f.file.name, f.data_pipeline.uuid) for f in deleted_files]
    
    task = rag_update.delay(added_files_serialized, updated_files_serialized, deleted_files_serialized, pipeline_url_changes, url_data_pipeline_uuid)

    # Wait for the task to complete
    result = AsyncResult(task.id)
    result.wait()
    # rag_update.delay(added_files_serialized, updated_files_serialized, deleted_files_serialized,pipeline_url_changes,url_data_pipeline_uuid)
    # test_rag_update(added_files_serialized, updated_files_serialized, deleted_files_serialized,pipeline_url_changes,url_data_pipeline_uuid)
    _thread_locals.added_files.clear()
    _thread_locals.deleted_files.clear()
    _thread_locals.updated_files.clear()
    _thread_locals.pipeline_url_changes = None
    _thread_locals.pipeline_instance = None
    _thread_locals.registered_for_commit = False

# Trigger RAG update at the end of the transaction
def rag_update_on_commit():
    has_changes = (
        _thread_locals.added_files or 
        _thread_locals.deleted_files or 
        _thread_locals.updated_files or 
        _thread_locals.pipeline_url_changes is not None
    )

    if not has_changes or _thread_locals.registered_for_commit:
        return

    _thread_locals.registered_for_commit = True
    transaction.on_commit(process_changes)

# Signal to handle file addition (post_save)
@receiver(post_save, sender=DataSource)
def on_file_added(sender, instance, created, **kwargs):
    init_file_changes()
    if created:
        _thread_locals.added_files.append(instance)
    rag_update_on_commit()

# Signal to handle file deletion (post_delete)
@receiver(post_delete, sender=DataSource)
def on_file_deleted(sender, instance, **kwargs):
    # Skip if DataPipeline deletion is in progress
    if getattr(_thread_locals, 'is_pipeline_deleting', False):
        return

    init_file_changes()
    _thread_locals.deleted_files.append(instance)
    rag_update_on_commit()

# Signal to handle file update (pre_save)
@receiver(pre_save, sender=DataSource)
def on_file_updated(sender, instance, **kwargs):
    init_file_changes()
    if instance.pk:
        try:
            old_instance = DataSource.objects.get(pk=instance.pk)
        except DataSource.DoesNotExist:
            old_instance = None

        if old_instance and old_instance.file != instance.file:
            _thread_locals.updated_files.append(instance)
            _thread_locals.deleted_files.append(old_instance)
    
    rag_update_on_commit()

# Signal to handle DataPipeline URL changes
@receiver(pre_save, sender=DataPipeline)
def on_pipeline_url_change(sender, instance, **kwargs):
    init_file_changes()
    if instance.pk:
        try:
            old_instance = DataPipeline.objects.get(pk=instance.pk)
        except DataPipeline.DoesNotExist:
            old_instance = None

        if old_instance and old_instance.url != instance.url:
            _thread_locals.pipeline_url_changes = (old_instance.url, instance.url)
            _thread_locals.pipeline_instance = instance
    else:
        if instance.url:
            _thread_locals.pipeline_url_changes = (None, instance.url)
            _thread_locals.pipeline_instance = instance
    rag_update_on_commit()

# Signal to set and unset the deletion flag for DataPipeline
@receiver(pre_delete, sender=DataPipeline)
def before_pipeline_delete(sender, instance, **kwargs):
    _thread_locals.is_pipeline_deleting = True  # Set flag before deletion

@receiver(post_delete, sender=DataPipeline)
def after_pipeline_delete(sender, instance, **kwargs):
    _thread_locals.is_pipeline_deleting = False  # Reset flag after deletion
