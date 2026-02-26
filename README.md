# Financial Document Analyzer
### AI-Powered CrewAI Debug Assignment — Complete Solution
**Submitted by:** Sannidhay Jangam | Wingify / VWO AI Internship 2026

---

## 🔗 Project Links

| | Link |
|---|---|
| 🌐 **Live App** | https://sannidhay-jangam-winifigy-assignment.netlify.app/ |
| 🖥️ **Frontend Repo** | https://github.com/sannidhayj20/Winfigy-front-end |
| ⚙️ **Backend Repo** | https://github.com/sannidhayj20/Wingify-crewai-correct-code |

---

## 📋 Project Overview

A full-stack AI-powered financial document analysis system. It accepts PDF financial reports (e.g., Tesla Q2 2025), processes them through a multi-agent CrewAI pipeline, and returns structured investment analysis, risk assessment, and market insights via a REST API.

The assignment required identifying and fixing two categories of issues:
- **Deterministic bugs** — broken Python/code logic causing crashes or incorrect behaviour
- **Inefficient prompts** — agent goals and backstories designed to produce hallucinated, harmful, or useless output

Both categories have been fully resolved.

---

## 🏗️ System Architecture

```
User (Browser)
    │
    ▼
React Frontend (Netlify)
    │  ├── Nhost Auth (email/password)
    │  ├── Apollo GraphQL Subscription (live status)
    │  └── POST /analyze (file upload + query)
    │
    ▼
FastAPI Backend (Render)
    │  └── CrewAI Pipeline (sequential)
    │        ├── Agent 1: Financial Analyst
    │        ├── Agent 2: Document Verifier
    │        ├── Agent 3: Investment Advisor
    │        └── Agent 4: Risk Assessor
    │
    ▼
Nhost / Hasura / PostgreSQL
    └── Stores results, streams status via GraphQL subscription
```

---

## 🐛 Bugs Found & Fixed

### `agents.py`

#### Bug 1 — LLM not initialised before use
```python
# Buggy
llm = llm  # NameError — self-referential, undefined variable

# Fixed
from langchain_openai import ChatOpenAI
llm = ChatOpenAI(model="gpt-4o-mini", api_key=os.getenv("OPENAI_API_KEY"))
```

#### Bug 2 — Wrong keyword argument (`tool` vs `tools`)
```python
# Buggy
tool=[FinancialDocumentTool.read_data_tool]   # silently ignored

# Fixed
tools=[FinancialDocumentTool.read_data_tool]  # correct kwarg name
```

#### Bug 3 — Harmful / non-compliant agent prompts (all 4 agents)
Every agent's `goal` and `backstory` was intentionally written to produce hallucinated, regulatory-non-compliant financial advice:
- `financial_analyst` — told to "make up investment advice" and ignore documents
- `verifier` — told to approve everything without reading files
- `investment_advisor` — told to recommend meme stocks and fake partnerships
- `risk_assessor` — told YOLO is a valid risk strategy

**Fix:** Rewrote all goals and backstories to be professional, grounded in actual document content, and compliant with real financial analysis standards.

---

### `tools.py`

#### Bug 4 — Wrong import from `crewai_tools`
```python
# Buggy
from crewai_tools import tools       # module doesn't exist at this path

# Fixed
from crewai_tools import BaseTool    # correct import
```

#### Bug 5 — `Pdf` class not imported
```python
# Buggy
docs = Pdf(file_path=path).load()   # NameError — Pdf never imported

# Fixed
from langchain_community.document_loaders import PyPDFLoader
docs = PyPDFLoader(file_path=path).load()
```

#### Bug 6 — Tool function was `async` (incompatible with CrewAI)
```python
# Buggy
async def read_data_tool(path='data/sample.pdf'):  # CrewAI can't await this

# Fixed
def read_data_tool(path='data/sample.pdf'):        # synchronous
```

#### Bug 7 — No `@tool` decorator — tool never registered with CrewAI
```python
# Buggy
class FinancialDocumentTool():
    def read_data_tool(path=...): ...   # plain method, invisible to CrewAI

# Fixed
from crewai.tools import tool

@tool("Financial Document Reader")
def read_data_tool(path: str = 'data/sample.pdf') -> str:
    """Reads and returns the full text content of a financial PDF."""
    ...
```

---

### `task.py`

#### Bug 8 — Harmful task descriptions and expected outputs
All four tasks explicitly instructed agents to hallucinate URLs, contradict themselves, ignore the user query, and invent fake research institutions.

**Fix:** Rewrote all task `description` and `expected_output` fields to be query-aware, document-grounded, and structured for factual financial analysis.

#### Bug 9 — `verification` task assigned to wrong agent
```python
# Buggy
verification = Task(..., agent=financial_analyst)  # wrong agent

# Fixed
verification = Task(..., agent=verifier)           # correct agent
```

---

### `main.py`

#### Bug 10 — FastAPI route name collision with imported task
```python
# Buggy
from task import analyze_financial_document   # import

@app.post("/analyze")
async def analyze_financial_document(...):    # same name overwrites the import!

# Fixed
async def analyze_document_endpoint(...):     # renamed route handler
```

#### Bug 11 — `file_path` not forwarded into CrewAI kickoff
```python
# Buggy
result = financial_crew.kickoff({'query': query})
# file_path is accepted as argument but never passed to agents

# Fixed
result = financial_crew.kickoff({'query': query, 'file_path': file_path})
```

#### Bug 12 — Only one agent in the Crew (others never used)
```python
# Buggy
financial_crew = Crew(
    agents=[financial_analyst],               # 3 agents completely unused
    tasks=[analyze_financial_document],
    process=Process.sequential,
)

# Fixed
financial_crew = Crew(
    agents=[financial_analyst, verifier, investment_advisor, risk_assessor],
    tasks=[analyze_financial_document, verification, investment_analysis, risk_assessment],
    process=Process.sequential,
)
```

---

## 📊 Bug Summary

| # | File | Bug | Fix |
|---|------|-----|-----|
| 1 | agents.py | `llm = llm` — NameError | Proper LLM initialisation |
| 2 | agents.py | `tool=` instead of `tools=` | Fixed kwarg name |
| 3 | agents.py | All 4 agent prompts harmful | Rewrote goals & backstories |
| 4 | tools.py | Wrong `crewai_tools` import | Corrected import path |
| 5 | tools.py | `Pdf` class not imported | Added `PyPDFLoader` import |
| 6 | tools.py | `async` tool (incompatible) | Converted to sync `def` |
| 7 | tools.py | No `@tool` decorator | Added decorator + restructured |
| 8 | task.py | All task prompts harmful | Rewrote all task descriptions |
| 9 | task.py | Wrong agent for verify task | Changed to `agent=verifier` |
| 10 | main.py | Route name collision | Renamed route handler |
| 11 | main.py | `file_path` not forwarded | Added to kickoff inputs |
| 12 | main.py | Only 1 agent in Crew | All agents + tasks included |

---

## ⭐ Bonus Features Implemented

### Queue Worker Model (Async Status Pipeline)
Instead of blocking the HTTP response for 2–5 minutes while CrewAI runs:

1. Frontend uploads file → calls `POST /analyze` with `chat_id`
2. Backend immediately sets status `"pending"` in Hasura
3. CrewAI crew runs → updates status `"processing"` → `"completed"`
4. Frontend uses **Apollo GraphQL subscription** — UI updates live, zero polling needed

### Database Integration (Nhost / Hasura / PostgreSQL)
- All analysis results persisted in PostgreSQL via Hasura GraphQL
- Full chat history in sidebar — click any past analysis to view results
- Row-level security ensures users only see their own analyses

### Production Frontend (React / Netlify)
- VWO-style split-screen UI with real-time status badges
- Email/password auth, forgot password, session management via Nhost Auth
- CI/CD: GitHub → Netlify with all build warnings resolved

---

## ⚙️ Setup & Usage

### Backend

```bash
git clone https://github.com/sannidhayj20/Wingify-crewai-correct-code.git
cd Wingify-crewai-correct-code
pip install -r requirements.txt
```

Create `.env`:
```
OPENAI_API_KEY=your_openai_api_key
SERPER_API_KEY=your_serper_api_key
NHOST_SUBDOMAIN=your_nhost_subdomain
NHOST_REGION=your_nhost_region
```

Add financial PDF:
```bash
mkdir -p data
# Save Tesla Q2 2025 PDF as data/sample.pdf
# https://www.tesla.com/sites/default/files/downloads/TSLA-Q2-2025-Update.pdf
```

Run:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend

```bash
git clone https://github.com/sannidhayj20/Winfigy-front-end.git
cd Winfigy-front-end
npm install
npm start          # development
npm run build      # production
```

---

## 📡 API Documentation

### `GET /`
Health check.
```json
{ "message": "Financial Document Analyzer API is running" }
```

### `POST /analyze`
Analyzes a financial PDF through the multi-agent CrewAI pipeline.

| Parameter | Type | Description |
|-----------|------|-------------|
| `chat_id` | string | UUID of the Hasura chat record to update |
| `file_id` | string | Nhost file storage ID of the uploaded PDF |
| `user_id` | string | Authenticated user ID |
| `query` | string | Natural language question about the document |

**Response:**
```json
{
  "status": "success",
  "query": "Analyze revenue growth and key risks",
  "analysis": "[Full multi-agent analysis output]",
  "file_processed": "TSLA-Q2-2025.pdf"
}
```

---

*Submitted for Wingify / VWO AI Internship Assignment — 2026*
