# # from django.db.models.signals import post_save, post_delete, pre_save
# # from django.dispatch import receiver
# # from django.db import transaction
# # from .models import DataSource, DataPipeline
# # from django.utils import timezone

# # # Function to handle updated files (both added and deleted)
# # def update_rag_files(added_files, deleted_files):
# #     print("Updating RAG with added files:", [(file.name, pipeline.name) for file, pipeline in added_files])
# #     print("Updating RAG with deleted files:", [(file.name, pipeline.name) for file, pipeline in deleted_files])

# # # Function to handle added files
# # def add_rag_file(added_files):
# #     print("Adding RAG files:", [(file.name, pipeline.name) for file, pipeline in added_files])

# # # Function to handle deleted files
# # def delete_rag_file(deleted_files):
# #     print("Deleting RAG files:", [(file.name, pipeline.name) for file, pipeline in deleted_files])

# # # Signal to handle file addition (post_save)
# # @receiver(post_save, sender=DataSource)
# # def on_file_added(sender, instance, created, **kwargs):
# #     if created:
# #         added_files = [(instance.file, instance.data_pipeline)]  # Store tuple of (file, data_pipeline)
# #         transaction.on_commit(lambda: trigger_rag_update(added_files=added_files, deleted_files=[]))
        
# #         # Update the status of the associated DataPipeline to 'pending'
# #         instance.data_pipeline.status = 'pending'
# #         instance.data_pipeline.updated_at = timezone.now()
# #         instance.data_pipeline.save()

# # # Signal to handle file deletion (post_delete)
# # @receiver(post_delete, sender=DataSource)
# # def on_file_deleted(sender, instance, **kwargs):
# #     deleted_files = [(instance.file, instance.data_pipeline)]  # Store tuple of (file, data_pipeline)
# #     transaction.on_commit(lambda: trigger_rag_update(added_files=[], deleted_files=deleted_files))
    
# #     # Update the status of the associated DataPipeline to 'pending'
# #     instance.data_pipeline.status = 'pending'
# #     instance.data_pipeline.updated_at = timezone.now()
# #     instance.data_pipeline.save()

# # # Signal to handle file update (pre_save)
# # @receiver(pre_save, sender=DataSource)
# # def on_file_updated(sender, instance, **kwargs):
# #     # Check if this is an update (not creation)
# #     if instance.pk:
# #         try:
# #             old_instance = DataSource.objects.get(pk=instance.pk)
# #         except DataSource.DoesNotExist:
# #             old_instance = None

# #         if old_instance and old_instance.file != instance.file:
# #             # File has been updated
# #             added_files = [(instance.file, instance.data_pipeline)]
# #             deleted_files = [(old_instance.file, old_instance.data_pipeline)]
# #             transaction.on_commit(lambda: trigger_rag_update(added_files=added_files, deleted_files=deleted_files))
            
# #             # Update the status of the associated DataPipeline to 'pending'
# #             instance.data_pipeline.status = 'pending'
# #             instance.data_pipeline.updated_at = timezone.now()
# #             instance.data_pipeline.save()

# # # Function to trigger RAG update
# # def trigger_rag_update(added_files, deleted_files):
# #     if added_files and deleted_files:
# #         update_rag_files(added_files, deleted_files)
# #     elif added_files:
# #         add_rag_file(added_files)
# #     elif deleted_files:
# #         delete_rag_file(deleted_files)

# # @receiver(pre_save, sender=DataPipeline)
# # def data_pipeline_url_changed(sender, instance, **kwargs):
# #     # Check if it's an update (not a creation)
# #     if instance.pk:
# #         try:
# #             old_instance = DataPipeline.objects.get(pk=instance.pk)
# #         except DataPipeline.DoesNotExist:
# #             old_instance = None
        
# #         # Check if the URL has been updated
# #         if old_instance and old_instance.url != instance.url:
# #             print(f"Old URL: {old_instance.url}")
# #             print(f"New URL: {instance.url}")
# #             instance.updated_at = timezone.now()
# #     else:
# #         # New instance being created
# #         print(f"A new pipeline '{instance.name}' is being created with URL: {instance.url}")
# #         if instance.url:
# #             print(f"New URL: {instance.url}")






# # # @receiver(pre_save, sender=DataPipeline)
# # # def data_pipeline_url_changed(sender, instance, **kwargs):
# # #     """
# # #     Signal handler that triggers when the DataPipeline is about to be saved, allowing us to compare the old URL with the new one.
# # #     """
# # #     # Check if the instance already exists (i.e., it's an update, not a creation)
# # #     if instance.pk:
# # #         try:
# # #             # Fetch the previous instance from the database to get the old URL
# # #             previous_instance = sender.objects.get(pk=instance.pk)
# # #             print(previous_instance.url, instance.url, "previous_instance.url != instance.url")
# # #             if previous_instance.url != instance.url:
# # #                 print(f"URL changed for pipeline '{instance.name}':")
# # #                 print(f"Old URL: {previous_instance.url}")
# # #                 print(f"New URL: {instance.url}")
# # #                 instance.updated_at = timezone.now()
# # #         except sender.DoesNotExist:
# # #             print(f"Previous instance of DataPipeline with ID {instance.pk} does not exist.")
# # #     else:
# # #         # New instance being created
# # #         print(f"A new pipeline '{instance.name}' is being created with URL: {instance.url}")





# from django.db.models.signals import post_save, post_delete, pre_save
# from django.dispatch import receiver
# from django.db import transaction
# from threading import local
# from .models import DataSource, DataPipeline
# from django.utils import timezone
# import time
# # Thread-local storage for tracking added, updated, and deleted files
# _thread_locals = local()

# # Initialize thread-local variables if they do not exist
# def init_file_changes():
#     if not hasattr(_thread_locals, 'added_files'):
#         _thread_locals.added_files = []
#     if not hasattr(_thread_locals, 'deleted_files'):
#         _thread_locals.deleted_files = []
#     if not hasattr(_thread_locals, 'updated_files'):
#         _thread_locals.updated_files = []
#     if not hasattr(_thread_locals, 'pipeline_url_changes'):
#         _thread_locals.pipeline_url_changes = None
#     if not hasattr(_thread_locals, 'registered_for_commit'):
#         _thread_locals.registered_for_commit = False  # Flag to avoid multiple registrations

# # Dummy function to handle accumulated changes
# def process_changes():
#     time.sleep(10)
#     added_files = getattr(_thread_locals, 'added_files', [])
#     deleted_files = getattr(_thread_locals, 'deleted_files', [])
#     updated_files = getattr(_thread_locals, 'updated_files', [])
#     pipeline_url_changes = getattr(_thread_locals, 'pipeline_url_changes', None)

#     print("Processing Changes")
#     print(f"Added Files: {[(f.file.name, f.data_pipeline.name) for f in added_files]}")
#     print(f"Deleted Files: {[(f.file.name, f.data_pipeline.name) for f in deleted_files]}")
#     print(f"Updated Files: {[(f.file.name, f.data_pipeline.name) for f in updated_files]}")

#     if pipeline_url_changes:
#         old_url, new_url = pipeline_url_changes
#         print(f"Pipeline URL Changed from {old_url} to {new_url}")

#     # Clear thread-local storage after processing
#     _thread_locals.added_files.clear()
#     _thread_locals.deleted_files.clear()
#     _thread_locals.updated_files.clear()
#     _thread_locals.pipeline_url_changes = None
#     _thread_locals.registered_for_commit = False  # Reset flag after processing

# # Trigger RAG update at the end of the transaction
# def rag_update_on_commit():
#     if _thread_locals.registered_for_commit:
#         # If this has already been registered, don't re-register
#         return
#     _thread_locals.registered_for_commit = True  # Set the flag to avoid multiple registrations
#     transaction.on_commit(process_changes)

# # Signal to handle file addition (post_save)
# @receiver(post_save, sender=DataSource)
# def on_file_added(sender, instance, created, **kwargs):
#     init_file_changes()
#     if created:
#         _thread_locals.added_files.append(instance)
    
#     # Update DataPipeline status
#     instance.data_pipeline.status = 'pending'
#     instance.data_pipeline.updated_at = timezone.now()
#     instance.data_pipeline.save()

#     # Register the callback to be executed after the transaction is committed
#     rag_update_on_commit()

# # Signal to handle file deletion (post_delete)
# @receiver(post_delete, sender=DataSource)
# def on_file_deleted(sender, instance, **kwargs):
#     init_file_changes()
#     _thread_locals.deleted_files.append(instance)

#     # Update DataPipeline status
#     instance.data_pipeline.status = 'pending'
#     instance.data_pipeline.updated_at = timezone.now()
#     instance.data_pipeline.save()

#     # Register the callback to be executed after the transaction is committed
#     rag_update_on_commit()

# # Signal to handle file update (pre_save)
# @receiver(pre_save, sender=DataSource)
# def on_file_updated(sender, instance, **kwargs):
#     init_file_changes()
#     if instance.pk:
#         try:
#             old_instance = DataSource.objects.get(pk=instance.pk)
#         except DataSource.DoesNotExist:
#             old_instance = None

#         if old_instance and old_instance.file != instance.file:
#             # Track updated files
#             _thread_locals.updated_files.append(instance)
#             _thread_locals.deleted_files.append(old_instance)

#     # Update DataPipeline status
#     instance.data_pipeline.status = 'pending'
#     instance.data_pipeline.updated_at = timezone.now()
#     instance.data_pipeline.save()

#     # Register the callback to be executed after the transaction is committed
#     rag_update_on_commit()

# # Signal to handle DataPipeline URL changes
# @receiver(pre_save, sender=DataPipeline)
# def on_pipeline_url_change(sender, instance, **kwargs):
#     init_file_changes()
#     if instance.pk:
#         try:
#             old_instance = DataPipeline.objects.get(pk=instance.pk)
#         except DataPipeline.DoesNotExist:
#             old_instance = None

#         if old_instance and old_instance.url != instance.url:
#             # Track URL changes
#             _thread_locals.pipeline_url_changes = (old_instance.url, instance.url)

#     # Register the callback to be executed after the transaction is committed
#     rag_update_on_commit()








from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.db import transaction
from threading import local
from ..models import DataSource, DataPipeline
from django.utils import timezone
import time
from ..tasks import rag_update

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

# Dummy function to handle accumulated changes
# Updated process_changes function
# def process_changes():
#     # time.sleep(10)
#     added_files = getattr(_thread_locals, 'added_files', [])
#     deleted_files = getattr(_thread_locals, 'deleted_files', [])
#     updated_files = getattr(_thread_locals, 'updated_files', [])
#     pipeline_url_changes = getattr(_thread_locals, 'pipeline_url_changes', None)
#     pipeline_instance = getattr(_thread_locals, 'pipeline_instance', None)

#     print("Processing Changes")
#     print(f"Added Files: {[(f.file.name, f.data_pipeline.name) for f in added_files]}")
#     print(f"Deleted Files: {[(f.file.name, f.data_pipeline.name) for f in deleted_files]}")
#     print(f"Updated Files: {[(f.file.name, f.data_pipeline.name) for f in updated_files]}")

#     if pipeline_url_changes:
#         old_url, new_url = pipeline_url_changes
#         print(f"Pipeline URL Changed from {old_url} to {new_url}")

#     # Collect the pipelines from file changes
#     data_pipelines = set(instance.data_pipeline for instance in added_files + deleted_files + updated_files)
    
#     # Add the pipeline with the URL change
#     if pipeline_instance:
#         data_pipelines.add(pipeline_instance)
    
#     # Update status to 'pending' for each involved DataPipeline
#     for pipeline in data_pipelines:
#         pipeline.status = 'pending'
#         pipeline.updated_at = timezone.now()
#         pipeline.save()

#     # Call the Celery task
#     rag_update.delay(added_files, updated_files, deleted_files)

#     # Clear thread-local storage after processing
#     _thread_locals.added_files.clear()
#     _thread_locals.deleted_files.clear()
#     _thread_locals.updated_files.clear()
#     _thread_locals.pipeline_url_changes = None
#     _thread_locals.pipeline_instance = None  # Clear the stored pipeline instance
#     _thread_locals.registered_for_commit = False  # Reset flag after processing




# Assuming process_changes function exists in signals.py

from ..tasks import rag_update

def process_changes():
    # Collect data for the background task, extracting only the necessary fields
    added_files = [(f.file.name, f.data_pipeline.name) for f in _thread_locals.added_files]
    updated_files = [(f.file.name, f.data_pipeline.name) for f in _thread_locals.updated_files]
    deleted_files = [(f.file.name, f.data_pipeline.name) for f in _thread_locals.deleted_files]

    # Call the Celery task with serializable data
    rag_update.delay(added_files, updated_files, deleted_files)

    # Clear thread-local storage after processing
    _thread_locals.added_files.clear()
    _thread_locals.deleted_files.clear()
    _thread_locals.updated_files.clear()
    _thread_locals.pipeline_url_changes = None
    _thread_locals.registered_for_commit = False



# Trigger RAG update at the end of the transaction
# def rag_update_on_commit():
#     if _thread_locals.registered_for_commit:
#         # If this has already been registered, don't re-register
#         return
#     _thread_locals.registered_for_commit = True  # Set the flag to avoid multiple registrations
#     transaction.on_commit(process_changes)


# Trigger RAG update at the end of the transaction
def rag_update_on_commit():
    # Check if there are any changes to process
    has_changes = (
        _thread_locals.added_files or 
        _thread_locals.deleted_files or 
        _thread_locals.updated_files or 
        _thread_locals.pipeline_url_changes is not None
    )

    # If no changes, do not register the commit callback
    if not has_changes or _thread_locals.registered_for_commit:
        return

    # Register for transaction commit if changes are present and not already registered
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
            # Track updated files
            _thread_locals.updated_files.append(instance)
            _thread_locals.deleted_files.append(old_instance)
    
    rag_update_on_commit()

# Signal to handle DataPipeline URL changes
# @receiver(pre_save, sender=DataPipeline)
# def on_pipeline_url_change(sender, instance, **kwargs):
#     init_file_changes()
#     if instance.pk:
#         try:
#             old_instance = DataPipeline.objects.get(pk=instance.pk)
#         except DataPipeline.DoesNotExist:
#             old_instance = None

#         if old_instance and old_instance.url != instance.url:
#             # Track URL changes
#             _thread_locals.pipeline_url_changes = (old_instance.url, instance.url)

#     rag_update_on_commit()

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
            # Track URL changes and store the pipeline instance
            _thread_locals.pipeline_url_changes = (old_instance.url, instance.url)
            _thread_locals.pipeline_instance = instance  # Store the actual instance here

    rag_update_on_commit()
