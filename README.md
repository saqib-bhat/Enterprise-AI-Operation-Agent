# Enterprise AI Operations Agent

A production-oriented AI operations assistant that answers business questions using SQL analytics and document retrieval (RAG), with planning, verification, Docker support, and a FastAPI API.

## Features

- Agentic workflow: Planner → Tools → Response → Verification
- SQL/data analysis for operational questions
- RAG over company policies and SOP documents
- FAISS + Sentence Transformers for CPU-friendly retrieval
- Mock LLM for testing and Groq provider support
- FastAPI REST API
- Docker / Docker Compose
- Evidence-aware responses
- Automated test suite: **62 tests passing**

## Architecture

```text
                    USER
                      |
                      v
                  FastAPI
                      |
                      v
                LangGraph Agent
                      |
                      v
                   Planner
                      |
             +--------+--------+
             |                 |
             v                 v
            SQL               RAG
             |                 |
             v                 v
         SQLite          FAISS + ST
             |                 |
             +--------+--------+
                      |
                      v
                 Tool Results
                      |
                      v
              Response Generator
                      |
                      v
                  Verifier
                      |
              +-------+-------+
              |               |
            Valid          Invalid
              |               |
              v               v
        Final Answer      Retry/Refuse
```

## Project Structure

```text
ENTERPRISE AI OPERATIONS AGENT/
│
├── app/
│   ├── agent/
│   │   ├── graph.py
│   │   ├── planner.py
│   │   ├── tool_executor.py
│   │   ├── verifier.py
│   │   └── response.py
│   │
│   ├── api/
│   │   ├── main.py
│   │   └── routes/
│   │       └── chat.py
│   │
│   ├── llm/
│   │   └── providers.py
│   │
│   ├── rag/
│   │   ├── embeddings.py
│   │   ├── ingestion.py
│   │   └── retrieval.py
│   │
│   ├── tools/
│   │   └── data_analysis_tool.py
│   │
│   └── config.py
│
├── data/
│   ├── documents/
│   ├── raw/
│   ├── processed/
│   └── operations.db
│
├── vector_store/
│   ├── index.faiss
│   └── metadata.json
│
├── tests/
│
├── frontend/
│
├── scripts/
│
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── .dockerignore
└── README.md
```

## Tech Stack

**Python 3.12 · FastAPI · Uvicorn · LangGraph · SQLAlchemy · SQLite · Pandas · NumPy · Sentence Transformers · FAISS · PyTorch CPU · MLflow · Streamlit · Docker**

## Configuration

For a real LLM, create `.env` from `.env.example`:

```env
LLM_PROVIDER=groq
GROQ_API_KEY=your_api_key
GROQ_MODEL=llama-3.1-8b-instant
DATABASE_URL=sqlite:///./data/operations.db
VECTOR_STORE_PATH=./vector_store
LOG_LEVEL=INFO
```

Docker Compose currently uses mock mode:

```env
LLM_PROVIDER=mock
DATABASE_URL=sqlite:///./data/operations.db
VECTOR_STORE_PATH=./vector_store
LOG_LEVEL=INFO
```

## Run Locally

Activate the virtual environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

Run the API:

```powershell
uvicorn app.api.main:app --reload
```

Health check:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/health"
```

Chat example:

```powershell
Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/chat" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"query":"What was July revenue?"}'
```

## Run with Docker

```powershell
docker compose build app
docker compose up
```

Check the container:

```powershell
docker compose ps
```

Stop:

```powershell
docker compose down
```

The Docker image installs **CPU-only PyTorch**, avoiding unnecessary CUDA/NVIDIA packages.

## Example Queries

SQL:

```text
What was July revenue?
```

RAG:

```text
What is the inventory reorder policy?
```

The API returns the query, answer, tools used, evidence, verification result, and errors.

## RAG Pipeline

```text
Documents
   ↓
PDF/Text Ingestion
   ↓
Sentence Transformer Embeddings
   ↓
FAISS Index
   ↓
Semantic Retrieval
   ↓
Retrieved Evidence
   ↓
Response Generation
   ↓
Verification
```

## Testing

Run all tests:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Current result:

```text
62 passed
```

Check Git whitespace:

```powershell
git diff --check
```

## API

### `GET /health`

```json
{
  "status": "ok"
}
```

### `POST /chat`

Request:

```json
{
  "query": "What was July revenue?"
}
```

Response includes:

```json
{
  "query": "...",
  "answer": "...",
  "tools_used": ["sql"],
  "evidence": [],
  "verification": {},
  "errors": {}
}
```

## Current Status

| Component | Status |
|---|---|
| FastAPI | Working |
| Docker Compose | Working |
| SQL Tool | Working |
| RAG Retrieval | Working |
| CPU Embeddings | Working |
| Verification | Working |
| Tests | **62 passing** |

## Design Goals

- Evidence-grounded answers
- Clear separation of planning, tools, generation, and verification
- CPU-friendly deployment
- Containerized execution
- Testable components
- Easy LLM provider replacement

