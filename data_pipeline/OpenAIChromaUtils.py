import os
import stat
import traceback
import logging
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader,
    CSVLoader,
)
from langchain.schema import Document
from openai import OpenAI
from django.conf import settings
from chromadb.api.client import SharedSystemClient

# Configure logging
logger = logging.getLogger(__name__)

# Initialize OpenAI and environment variables
OPENAI_API_KEY = settings.OPENAI_API_KEY  # Use settings for Django integration

if not OPENAI_API_KEY:
    raise EnvironmentError("Please set the OPENAI_API_KEY environment variable in your Django settings.")

# Initialize the OpenAI embeddings
embeddings = OpenAIEmbeddings()

# Error Logging Function using Django's logger
def log_error(message, log_file=None):
    if log_file:
        # Optional: Write to a specific log file
        with open(log_file, 'w') as f:
            f.write(message)
    logger.error(message)  # Log to Django's logging system

def load_documents(file_paths, db_name, log_file=None):
    folder_path = os.path.join(settings.DATA_SOURCE_FOLDER, db_name)

    # Step 1: Create a new instance of Chroma for the collection
    chroma_db = Chroma(
        persist_directory=folder_path,
        embedding_function=embeddings,
        collection_name=f"{db_name}_collection",
    )

    documents = []
    error_messages = []
    try:
        # Step 3: Load new documents from the provided file paths
        for file_path in file_paths:
            file_path = os.path.join(settings.MEDIA_ROOT, file_path)
            ext = os.path.splitext(file_path)[1].lower()

            try:
                logger.info(f"Attempting to load file: {file_path}")
                docs = None

                if ext == ".pdf":
                    loader = PyPDFLoader(file_path)
                    docs = loader.load_and_split()
                elif ext == ".docx":
                    loader = Docx2txtLoader(file_path)
                    docs = loader.load_and_split()
                elif ext == ".txt":
                    docs = []
                    with open(file_path, 'r', encoding='utf-8') as f:
                        text = f.read()
                    for i in range(0, len(text), 500 - 100):
                        chunk = text[i:i + 500]
                        if chunk:
                            docs.append(Document(page_content=chunk))
                elif ext == ".csv":
                    loader = CSVLoader(file_path)
                    docs = loader.load_and_split()
                else:
                    logger.warning(f"Unsupported file type: {ext}")
                    continue
                

                collection = chroma_db.get()
                existing_docs = [
                    doc_id for doc_id, metadata in zip(collection["ids"], collection["metadatas"])
                    if metadata.get("file_path") == file_path
                ]
                
                if existing_docs:
                    logger.info(f"Found existing documents for {file_path}. Deleting old entries...")
                    chroma_db.delete(ids=existing_docs)
                    logger.info(f"Deleted {len(existing_docs)} documents for {file_path}.")
                
                # for doc in docs:
                #     doc.metadata = {"file_path": file_path, "client": db_name}
                #     documents.append(doc)

                # Check and filter out any documents with None or empty page_content
                valid_docs = [doc for doc in docs if doc.page_content and isinstance(doc.page_content, str) and doc.page_content.strip()]

                if not valid_docs:
                    logger.warning(f"No valid content found in {file_path}. Skipping.")
                    continue

                # Add metadata to the new documents
                for doc in valid_docs:
                    doc.metadata = {"file_path": file_path, "client": db_name}
                    documents.append(doc)

            except Exception as e:
                error_message = f"Error loading {file_path}: {str(e)}\n"
                logger.error(error_message)
                error_messages.append(error_message)
                traceback.print_exc()

        # Step 4: Add new documents to the existing collection without deleting it
        if documents:
            try:
                chroma_db.add_documents(documents)
                logger.info(f"Added {len(documents)} new documents to Chroma collection: {db_name}_collection.")
            except Exception as e:
                error_message = f"Error adding documents: {str(e)}\n"
                logger.error(error_message)
                error_messages.append(error_message)
                traceback.print_exc()
        # Step 5: Log any errors
        if error_messages:
            log_error("\n".join(error_messages), log_file=log_file)
    except Exception as e:
        error_message = f"Error adding documents: {str(e)}\n"
        logger.error(error_message)
    finally:
        if chroma_db:
            chroma_db._client._system.stop()
            SharedSystemClient._identifier_to_system.pop(chroma_db._client._identifier, None)    
            chroma_db = None

# Document Deletion Function
def delete_documents(file_paths, db_name, log_file=None):
    folder_path=os.path.join(settings.DATA_SOURCE_FOLDER, db_name)
    chroma_db = Chroma(
        persist_directory=folder_path,
        embedding_function=embeddings,
        collection_name=f"{db_name}_collection",
    )

    error_messages = []
    try:
        for file_path in file_paths:
            try:
                file_path=os.path.join(settings.MEDIA_ROOT, file_path)
                if os.path.exists(file_path):
                    os.chmod(file_path, stat.S_IWRITE)
                    os.remove(file_path)
                    logger.info(f"Deleted {file_path} from directory.")
                else:
                    logger.warning(f"File {file_path} does not exist in directory.")
                
                collection = chroma_db.get()
                logger.info("Collection retrieved from Chroma.")
                
                if 'metadatas' in collection and collection['metadatas']:
                    doc_ids_to_delete = [
                        doc_id
                        for doc_id, metadata in zip(collection["ids"], collection["metadatas"])
                        if metadata.get("file_path") == file_path
                    ]
                    
                    if doc_ids_to_delete:
                        chroma_db.delete(ids=doc_ids_to_delete)
                        logger.info(f"Deleted {len(doc_ids_to_delete)} documents from Chroma collection: {db_name}_collection.")
                    else:
                        logger.info(f"No documents found in Chroma collection for file {file_path}.")
                else:
                    logger.warning("No metadata found in the Chroma collection.")

            except Exception as e:
                error_message = f"Error deleting documents for file {file_path}: {str(e)}\n"
                logger.error(error_message)
                error_messages.append(error_message)
                traceback.print_exc()

        if error_messages:
            log_error("\n".join(error_messages), log_file=log_file)
    except Exception as e:
        error_message = f"Error deleting documents: {str(e)}\n"
        logger.error(error_message)
    finally:
        if chroma_db:
            chroma_db._client._system.stop()
            SharedSystemClient._identifier_to_system.pop(chroma_db._client._identifier, None)    
            chroma_db = None

def chat_with_documents(query, db_name=None, chat_history=None):
    try:
        # Initialize chat history if it's None
        if chat_history is None:
            chat_history = []

        # Only interact with Chroma if db_name is provided
        if db_name:
            folder_path = os.path.join(settings.DATA_SOURCE_FOLDER, db_name)

            # Reinitialize Chroma database from disk to ensure fresh data
            chroma_db = Chroma(
                persist_directory=folder_path,
                embedding_function=embeddings,
                collection_name=f"{db_name}_collection",
            )

            print(chroma_db, "chroma_db")

            # Create a retrieval QA chain with Chroma
            try:
                retriever = chroma_db.as_retriever(search_type="similarity", search_kwargs={"k": 5})
                relevant_docs = retriever.invoke(query)
                print(relevant_docs, "relevant_docs")
            except Exception as e:
                print("Exception: ", str(e))
                relevant_docs = []  # Ensure relevant_docs is defined in case of failure

            # Construct the context for messages with document content
            messages = [{"role": "system", "content": "\n".join([f"{doc.page_content}" for i, doc in enumerate(relevant_docs)])}]
        else:
            # If no database, set an empty list for relevant documents
            messages = [{"role": "system", "content": "No documents available for context."}]

        # Append the chat history and the user's query to the messages
        messages.extend(chat_history)
        messages.append({"role": "user", "content": query})
        # Initialize the OpenAI client
        client = OpenAI()

        try:
            # Stream the response from OpenAI
            completion = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                stream=True,
                temperature=0.5,
            )

            # Generator for streaming content
            def event_stream():
                for chunk in completion:
                    if hasattr(chunk, "choices") and chunk.choices:
                        delta = chunk.choices[0].delta
                        if delta and hasattr(delta, "content"):
                            content = delta.content
                            if content:
                                yield content

            return event_stream

        except Exception as e:
            error_message = f"Error during streaming: {str(e)}"
            logger.error(error_message)
            raise

    except Exception as e:
        error_message = f"Error adding documents: {str(e)}\n"
        logger.error(error_message)
    finally:
        if chroma_db:
            chroma_db._client._system.stop()
            SharedSystemClient._identifier_to_system.pop(chroma_db._client._identifier, None)    
            chroma_db = None

        