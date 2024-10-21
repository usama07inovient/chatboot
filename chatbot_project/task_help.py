from data_pipeline.tasks import rag_update

added_files = [("test_file.txt", "Pipeline A")]
updated_files = []
deleted_files = []

# Send the task asynchronously
result = rag_update.apply_async((added_files, updated_files, deleted_files))
print("Task sent:", result.id)


# [2024-10-08 17:26:22,864: INFO/MainProcess] Task data_pipeline.tasks.rag_update[4e66a3f7-528d-4d29-a3f5-b79c5bee0899] received
from celery.result import AsyncResult

# Replace this with your actual task ID
task_id = '4432b630-c231-4b0d-8c0e-14a323cfbddr'
result = AsyncResult(task_id)

# Check the status
print("Task Status:", result.status)

# If the task is finished, you can also retrieve the result
if result.status == 'SUCCESS':
    print("Task Result:", result.result)
