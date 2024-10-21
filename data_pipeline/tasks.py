from celery import shared_task
import time
from celery import current_app
from .models import DataSource, DataPipeline
import sys
import os
from .trigger_script import start_scraping
from .OpenAIChromaUtils import delete_documents,load_documents


def process_url_changes(pipeline_url_changes, url_data_pipeline_uuid):
    old_url, new_url = pipeline_url_changes
    
    # Define the path template for the data source file
    file_path_template = f"media/data_sources/{url_data_pipeline_uuid}/url_file.txt"
    print(new_url,"new_url")
    # Case: New URL is None, implying a deletion of the old file
    if new_url is None:
        # delete_old_file(file_path_template)
        delete_documents(file_paths=[file_path_template], db_name=url_data_pipeline_uuid, log_file=None)
    
    # Case: Old URL is None, implying we need to start scraping for the new URL
    elif old_url is None:
        start_scraping(new_url, file_path_template, max_links=None)
        file_path=os.path.join('data_sources', str(url_data_pipeline_uuid), 'url_file.txt')
        load_documents([file_path], str(url_data_pipeline_uuid), log_file=None)
    # Case: URL is updated, so delete the old file and scrape the new URL
    else:
        delete_documents(file_paths=[file_path_template], db_name=url_data_pipeline_uuid, log_file=None)
        # delete_old_file(file_path_template)
        start_scraping(new_url, file_path_template, max_links=None)
        file_path=os.path.join('data_sources', str(url_data_pipeline_uuid), 'url_file.txt')
        load_documents([file_path], str(url_data_pipeline_uuid), log_file=None)

# def delete_old_file(file_path):
#     """Deletes the specified file and the associated error file if they exist."""
#     # Define the path for the scraping_errors.txt file
#     error_file_path = os.path.join(os.path.dirname(file_path), 'scraping_errors.txt')
    
#     # Delete the main file (url_file.txt)
#     if os.path.exists(file_path):
#         os.remove(file_path)
#         print(f"Deleted old file at {file_path}")
#     else:
#         print(f"No file found at {file_path} to delete.")
    
#     # Delete the associated error file (scraping_errors.txt)
#     if os.path.exists(error_file_path):
#         os.remove(error_file_path)
#         print(f"Deleted error log file at {error_file_path}")
#     else:
#         print(f"No error log file found at {error_file_path} to delete.")


def scrape_new_url(url):
    """Placeholder function to scrape data from a new URL."""
    # Dummy function for URL scraping logic
    print(f"Scraping data from {url}")
    # Add scraping logic here, e.g., using BeautifulSoup or another library

@shared_task
def rag_update(added_files, updated_files, deleted_files, pipeline_url_changes, url_data_pipeline_uuid):
    
    # Ensure connection
    with current_app.pool.acquire(block=True) as conn:
        conn.ensure_connection()
    added_file_paths = [file_info[0] for file_info in added_files]
    updated_file_paths = [file_info[0] for file_info in updated_files]
    deleted_file_paths = [file_info[0] for file_info in deleted_files]
    
    added_file_paths.extend(updated_file_paths)
    
    if added_files:
        first_added_uuid = added_files[0][1]
    elif updated_files:
        first_added_uuid = updated_files[0][1]
    elif deleted_files:
        first_added_uuid = deleted_files[0][1]

    if added_file_paths:
        print(added_file_paths,"added_file_paths")
        load_documents(added_file_paths, str(first_added_uuid), log_file=None)
    # Process deleted files

    if deleted_file_paths:
        print(deleted_file_paths,"deleted_file_paths")
        delete_documents(deleted_file_paths, str(first_added_uuid), log_file=None)

    # for file_info in deleted_files:
    #     file_name, pipeline_name = file_info
    #     print(f"Processing deleted file: {file_name} for pipeline: {pipeline_name}")
    #     delete_documents(deleted_file_paths, str(first_added_uuid), log_file=None)
    

    data_pipelines_uuids = set(data_source[1] for data_source in added_files + deleted_files + updated_files)

    # Handle URL changes
    if pipeline_url_changes:
        print(pipeline_url_changes,"pipeline_url_changes")
        process_url_changes(pipeline_url_changes, str(url_data_pipeline_uuid))
        data_pipelines_uuids.add(url_data_pipeline_uuid)


    # Change status to active for each data pipeline
    for data_pipeline_uuid in data_pipelines_uuids:
        data_pipeline = DataPipeline.objects.filter(uuid=data_pipeline_uuid).first()
        data_pipeline.status = "active"
        data_pipeline.save()




def test_rag_update(added_files, updated_files, deleted_files, pipeline_url_changes, url_data_pipeline_uuid):
    
    added_file_paths = [file_info[0] for file_info in added_files]
    updated_file_paths = [file_info[0] for file_info in updated_files]
    deleted_file_paths = [file_info[0] for file_info in deleted_files]
    
    added_file_paths.extend(updated_file_paths)
    
    if added_files:
        first_added_uuid = added_files[0][1]
    elif updated_files:
        first_added_uuid = updated_files[0][1]
    elif deleted_files:
        first_added_uuid = deleted_files[0][1]

    if added_file_paths:
        print(added_file_paths,"added_file_paths")
        load_documents(added_file_paths, str(first_added_uuid), log_file=None)
    # Process deleted files

    if deleted_file_paths:
        print(deleted_file_paths,"deleted_file_paths")
        delete_documents(deleted_file_paths, str(first_added_uuid), log_file=None)

    # for file_info in deleted_files:
    #     file_name, pipeline_name = file_info
    #     print(f"Processing deleted file: {file_name} for pipeline: {pipeline_name}")
    #     delete_documents(deleted_file_paths, str(first_added_uuid), log_file=None)
    

    data_pipelines_uuids = set(data_source[1] for data_source in added_files + deleted_files + updated_files)

    # Handle URL changes
    if pipeline_url_changes:
        print(pipeline_url_changes,"pipeline_url_changes")
        process_url_changes(pipeline_url_changes, str(url_data_pipeline_uuid))
        data_pipelines_uuids.add(url_data_pipeline_uuid)


    # Change status to active for each data pipeline
    for data_pipeline_uuid in data_pipelines_uuids:
        data_pipeline = DataPipeline.objects.filter(uuid=data_pipeline_uuid).first()
        data_pipeline.status = "active"
        data_pipeline.save()
