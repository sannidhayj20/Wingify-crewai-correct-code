import os
import uuid
from fastapi import FastAPI, Request
from redis import Redis
from rq import Queue
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# 1. Enable CORS for your React Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace with your Netlify URL
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Connect to Redis (Use Render's REDIS_URL)
redis_conn = Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
q = Queue("financial_analysis", connection=redis_conn)

@app.post("/analyze")
async def analyze_document(request: Request):
    data = await request.json()
    
    # These IDs come from your React app's upload workflow
    chat_id = data.get("chat_id")
    file_id = data.get("file_id")
    user_id = data.get("user_id")
    user_query = data.get("query", "Analyze financial risks")

    # 3. Hand off to the background worker
    # We pass the IDs so the worker knows which file to get and which row to update
    job = q.enqueue(
        "tasks.background_analysis_task",
        chat_id,
        file_id,
        user_id,
        user_query
    )

    return {"status": "queued", "job_id": job.get_id()}