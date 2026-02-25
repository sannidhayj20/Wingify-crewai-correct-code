import os
import requests
from crew import WingifyCorrectCode
# Redis and Queue imports are handled by the worker CLI, 
# but keeping 'os' is critical for your config.

# --- CONFIGURATION ---
NHOST_SUBDOMAIN = os.getenv("NHOST_SUBDOMAIN")
HASURA_ADMIN_SECRET = os.getenv("HASURA_ADMIN_SECRET")
HASURA_URL = f"https://{NHOST_SUBDOMAIN}.nhost.run/v1/graphql"

def update_hasura_status(chat_id, status, result=None):
    """Updates the 'chats' table in Hasura with current progress."""
    mutation = """
    mutation UpdateChat($id: uuid!, $status: String!, $result: String) {
      update_chats_by_pk(pk_columns: {id: $id}, _set: {status: $status, analysis_result: $result}) {
        id
      }
    }
    """
    variables = {"id": chat_id, "status": status, "result": str(result) if result else None}
    try:
        response = requests.post(
            HASURA_URL,
            json={'query': mutation, 'variables': variables},
            headers={'x-hasura-admin-secret': HASURA_ADMIN_SECRET},
            timeout=10
        )
        response.raise_for_status()
        print(f"DEBUG: Hasura status updated to {status}")
    except Exception as e:
        print(f"ERROR: Failed to update Hasura: {e}")

def background_analysis_task(chat_id, file_id, user_id, user_query):
    """
    The main worker task logic.
    """
    print(f"--- WORKER START ---")
    print(f"Picking up Job for Chat: {chat_id}")
    
    # Update status to 'processing'
    update_hasura_status(chat_id, "processing")
    
    # Define a temporary path in the Koyeb container
    temp_pdf_path = f"/tmp/{file_id}.pdf"

    try:
        # 1. Download PDF from Nhost Storage
        file_url = f"https://{NHOST_SUBDOMAIN}.storage.nhost.run/v1/files/{file_id}"
        print(f"DEBUG: Downloading from Nhost Storage: {file_id}")

        response = requests.get(
            file_url, 
            headers={'x-hasura-admin-secret': HASURA_ADMIN_SECRET},
            stream=True
        )
        response.raise_for_status()

        with open(temp_pdf_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        print("DEBUG: PDF Downloaded. Initializing CrewAI...")

        # 2. Run CrewAI logic
        inputs = {'query': user_query, 'file_path': temp_pdf_path}
        crew_instance = WingifyCorrectCode().crew()
        result = crew_instance.kickoff(inputs=inputs)

        # 3. Success Update
        update_hasura_status(chat_id, "completed", result=result.raw)
        print(f"DONE: Analysis for {chat_id} uploaded to Hasura.")

    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        update_hasura_status(chat_id, "failed", result=f"Error: {str(e)}")

    finally:
        # Clean up the temp file
        if os.path.exists(temp_pdf_path):
            os.remove(temp_pdf_path)
            print("Cleanup: Temporary PDF deleted.")
