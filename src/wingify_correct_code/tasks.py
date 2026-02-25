import os
import requests
from crew import WingifyCorrectCode

# --- CONFIGURATION ---
# Subdomain confirmed: afpyjlwmrdbhahnyndhl
# Region confirmed: ap-south-1
NHOST_SUBDOMAIN = "afpyjlwmrdbhahnyndhl"
HASURA_ADMIN_SECRET = os.getenv("HASURA_ADMIN_SECRET")

# CONFIRMED URLS VIA CURL TEST
HASURA_URL = f"https://{NHOST_SUBDOMAIN}.hasura.ap-south-1.nhost.run/v1/graphql"
STORAGE_URL = f"https://{NHOST_SUBDOMAIN}.storage.ap-south-1.nhost.run/v1/files"

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
            timeout=15
        )
        response.raise_for_status()
        print(f"DEBUG: Hasura status updated to '{status}'")
    except Exception as e:
        print(f"ERROR: Failed to update Hasura: {e}")

def background_analysis_task(chat_id, file_id, user_id, user_query):
    print(f"--- WORKER START ---")
    
    # 1. Update status to 'processing'
    update_hasura_status(chat_id, "processing")
    
    temp_pdf_path = f"/tmp/{file_id}.pdf"

    try:
        # 2. Download PDF using the confirmed STORAGE_URL
        file_url = f"{STORAGE_URL}/{file_id}"
        print(f"DEBUG: Downloading from: {file_url}")
        
        response = requests.get(
            file_url, 
            headers={'x-hasura-admin-secret': HASURA_ADMIN_SECRET},
            stream=True
        )
        response.raise_for_status()

        with open(temp_pdf_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print("DEBUG: PDF Download successful. Starting CrewAI analysis...")

        # 3. Run CrewAI Logic
        inputs = {'query': user_query, 'file_path': temp_pdf_path}
        crew_instance = WingifyCorrectCode().crew()
        result = crew_instance.kickoff(inputs=inputs)

        # 4. Success Update
        update_hasura_status(chat_id, "completed", result=result.raw)
        print(f"--- WORKER SUCCESS: Chat {chat_id} finished ---")

    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        update_hasura_status(chat_id, "failed", result=f"Error: {str(e)}")
    
    finally:
        if os.path.exists(temp_pdf_path):
            os.remove(temp_pdf_path)
            print("Cleanup: Temporary file deleted.")
