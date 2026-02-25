import os
import requests
from crew import WingifyCorrectCode

# --- CONFIGURATION ---
# These must be set in your Koyeb Environment Variables
NHOST_SUBDOMAIN = os.getenv("NHOST_SUBDOMAIN") # e.g., afpyjlwmrdbhahnyndhl
HASURA_ADMIN_SECRET = os.getenv("HASURA_ADMIN_SECRET")

# CORRECT NHOST URL STRUCTURE (No extra .run in middle)
# Subdomain.graphql.nhost.run for Hasura
HASURA_URL = "https://afpyjlwmrdbhahnyndhl.hasura.ap-south-1.nhost.run/v1/graphql"
# Subdomain.storage.nhost.run for Files
STORAGE_URL = f"https://{NHOST_SUBDOMAIN}.storage.nhost.run/v1/files"

def update_hasura_status(chat_id, status, result=None):
    """
    Updates the 'chats' table in Hasura with current progress.
    Defined at the top to avoid NameError.
    """
    mutation = """
    mutation UpdateChat($id: uuid!, $status: String!, $result: String) {
      update_chats_by_pk(pk_columns: {id: $id}, _set: {status: $status, analysis_result: $result}) {
        id
      }
    }
    """
    variables = {
        "id": chat_id, 
        "status": status, 
        "result": str(result) if result else None
    }
    
    try:
        response = requests.post(
            HASURA_URL,
            json={'query': mutation, 'variables': variables},
            headers={'x-hasura-admin-secret': HASURA_ADMIN_SECRET},
            timeout=15
        )
        response.raise_for_status()
        print(f"DEBUG: Hasura status updated to '{status}' for chat {chat_id}")
    except Exception as e:
        print(f"ERROR: Failed to update Hasura: {e}")

def background_analysis_task(chat_id, file_id, user_id, user_query):
    """
    Main worker task logic.
    """
    print(f"--- WORKER START ---")
    print(f"Chat: {chat_id} | File: {file_id}")

    # 1. Update status to 'processing'
    update_hasura_status(chat_id, "processing")
    
    temp_pdf_path = f"/tmp/{file_id}.pdf"

    try:
        # 2. Download PDF from Nhost Storage
        file_url = f"{STORAGE_URL}/{file_id}"
        print(f"DEBUG: Requesting download from: {file_url}")
        
        response = requests.get(
            file_url, 
            headers={'x-hasura-admin-secret': HASURA_ADMIN_SECRET},
            stream=True
        )
        response.raise_for_status()

        with open(temp_pdf_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print("DEBUG: PDF download successful. Running CrewAI...")

        # 3. Run CrewAI Logic
        inputs = {
            'query': user_query,
            'file_path': temp_pdf_path
        }

        crew_instance = WingifyCorrectCode().crew()
        result = crew_instance.kickoff(inputs=inputs)

        # 4. Success: Upload final result
        update_hasura_status(chat_id, "completed", result=result.raw)
        print(f"--- WORKER SUCCESS: Chat {chat_id} finished ---")

    except Exception as e:
        print(f"--- WORKER CRITICAL ERROR ---")
        print(f"Details: {str(e)}")
        update_hasura_status(chat_id, "failed", result=f"Error: {str(e)}")
    
    finally:
        # Cleanup temp file to prevent disk fill-up on Koyeb
        if os.path.exists(temp_pdf_path):
            os.remove(temp_pdf_path)
            print("DEBUG: Temporary file deleted.")
