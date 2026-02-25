import os
import requests
from crew import WingifyCorrectCode
from redis import Redis
from rq import Queue

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
    except Exception as e:
        print(f"Failed to update Hasura: {e}")

def background_analysis_task(chat_id, file_id, user_id, user_query):
    """
    The main worker task: 
    1. Downloads the PDF from Nhost.
    2. Runs your WingifyCorrectCode Crew.
    3. Updates Hasura with the final report.
    """
    # 1. Update status to 'processing'
    update_hasura_status(chat_id, "processing")
    
    # Define a temporary path on the Render server
    temp_pdf_path = f"/tmp/{file_id}.pdf"

    try:
        # 2. Download PDF from Nhost Storage
        # We use the admin secret to bypass storage permissions on the backend
        file_url = f"https://{NHOST_SUBDOMAIN}.storage.nhost.run/v1/files/{file_id}"
        print(f"Downloading file {file_id}...")
        
        response = requests.get(
            file_url, 
            headers={'x-hasura-admin-secret': HASURA_ADMIN_SECRET},
            stream=True
        )
        response.raise_for_status()

        with open(temp_pdf_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        # 3. Initialize and Run your CrewAI logic
        print(f"Starting CrewAI analysis for Query: {user_query}")
        
        # We pass the dynamic temp_pdf_path instead of your local D: drive path
        inputs = {
            'query': user_query,
            'file_path': temp_pdf_path
        }

        crew_instance = WingifyCorrectCode().crew()
        result = crew_instance.kickoff(inputs=inputs)

        # 4. Success! Update status to 'completed' with the raw result
        update_hasura_status(chat_id, "completed", result=result.raw)
        print("Analysis complete and database updated.")

    except Exception as e:
        print(f"Error in background task: {e}")
        update_hasura_status(chat_id, "failed", result=f"Error: {str(e)}")
    
    finally:
        # Clean up the temp file to save disk space on Render
        if os.path.exists(temp_pdf_path):
            os.remove(temp_pdf_path)