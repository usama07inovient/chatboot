from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chatbot_project.settings')

app = Celery('chatbot_project')

# Using a string here means the worker doesn’t have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()









# # Get active tasks
# active_tasks = app.control.inspect().active()
# reserved_tasks = app.control.inspect().reserved()

# # Display results
# print("Active Tasks:",active_tasks)
# print("\nReserved Tasks:",reserved_tasks)


# def get_unfinished_tasks():
#     inspector = app.control.inspect()
    
#     # Get active tasks
#     active_tasks = inspector.active() or {}
#     reserved_tasks = inspector.reserved() or {}
#     scheduled_tasks = inspector.scheduled() or {}
    
#     unfinished_tasks = {
#         'active': active_tasks,
#         'reserved': reserved_tasks,
#         'scheduled': scheduled_tasks
#     }
    
#     return unfinished_tasks

# # Call the function to get unfinished tasks
# unfinished_tasks = get_unfinished_tasks()
# print("Unfinished Tasks:", unfinished_tasks)



@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
