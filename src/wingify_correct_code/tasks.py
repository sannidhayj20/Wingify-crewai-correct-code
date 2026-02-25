import os
import requests
from crew import WingifyCorrectCode
from redis import Redis

NHOST_SUBDOMAIN = os.getenv("NHOST_SUBDOMAIN")
HASURA_ADMIN_SECRET = os.getenv("HASURA_ADMIN_SECRET")
HASURA_URL = f"https://{NHOST_SUBDOMAIN}.nhost.run/v1/graphql"

def background_analysis_task(chat_id, file_id, user_id, user_query):
    print(f"--- WORKER START ---")
    print(f"Picking up Job for Chat: {chat_id}")
    
    update_hasura_status(chat_id, "processing")
    temp_pdf_path = f"/tmp/{file_id}.pdf"

    try:
        # Download...
        file_url = f"https://{NHOST_SUBDOMAIN}.storage.nhost.run/v1/files/{file_id}"
        print(f"Downloading from Nhost Storage: {file_id}")
        
        response = requests.get(
            file_url, 
            headers={'x-hasura-admin-secret': HASURA_ADMIN_SECRET},
            stream=True
        )
        response.raise_for_status()

        with open(temp_pdf_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        print("PDF Downloaded. Initializing CrewAI...")
        
        inputs = {'query': user_query, 'file_path': temp_pdf_path}
        crew_instance = WingifyCorrectCode().crew()
        result = crew_instance.kickoff(inputs=inputs)

        update_hasura_status(chat_id, "completed", result=result.raw)
        print(f"DONE: Analysis for {chat_id} uploaded to Hasura.")

    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        update_hasura_status(chat_id, "failed", result=f"Error: {str(e)}")
    
    finally:
        if os.path.exists(temp_pdf_path):
            os.remove(temp_pdf_path)
            print("Cleanup: Temporary PDF deleted.")
