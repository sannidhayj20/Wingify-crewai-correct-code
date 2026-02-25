import os
from fastapi import FastAPI, Request
from redis import Redis
from rq import Queue
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

# Use 'rediss://' for Upstash Secure TCP
REDIS_URL = os.getenv("REDIS_URL")
# ssl_cert_reqs=None is often required for cloud-to-cloud SSL handshakes
redis_conn = Redis.from_url(REDIS_URL, ssl_cert_reqs=None)
q = Queue("financial_analysis", connection=redis_conn)

@app.post("/analyze")
async def analyze_document(request: Request):
    data = await request.json()
    chat_id = data.get("chat_id")
    file_id = data.get("file_id")
    user_query = data.get("query", "Analyze financial risks")

    print(f"--- API RECEIVE ---")
    print(f"Chat ID: {chat_id} | File ID: {file_id}")

    # Hand off to the Koyeb worker via Upstash
    job = q.enqueue(
        "tasks.background_analysis_task",
        chat_id,
        file_id,
        data.get("user_id"),
        user_query
    )

    print(f"SUCCESS: Job {job.id} pushed to Upstash (Mumbai).")
    return {"status": "queued", "job_id": job.get_id()}
