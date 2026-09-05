# Enterprise AI Operations Agent

A production-oriented AI operations assistant that answers business questions using SQL analytics and document retrieval (RAG), with planning, verification, Docker support, and a FastAPI API.

## Features

- Agentic workflow: Planner → Router → Tools → Evidence → Verification → Response
- SQL/data analysis for operational questions
- RAG over company policies and SOP documents
- FAISS + Sentence Transformers for CPU-friendly retrieval
- Mock LLM for testing and Groq provider support
- FastAPI REST API
- Docker / Docker Compose
- Evidence-aware responses
- Automated test suite: **62 tests passing**
- RAG evaluation: **85% Hit@1 and 100% Hit@3** across 20 policy and SOP queries

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
           Final Answer        Refuse
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
│   │   ├── calculator_tool.py
│   │   ├── data_analysis_tool.py
│   │   └── sql_tool.py
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

For local development without API costs, use mock mode. For natural-language responses, configure Groq in `.env`:

```env
LLM_PROVIDER=groq
GROQ_API_KEY=your_api_key
GROQ_MODEL=llama-3.1-8b-instant
DATABASE_URL=sqlite:///./data/operations.db
VECTOR_STORE_PATH=./vector_store
LOG_LEVEL=INFO
```

Never commit `.env` or API keys. `.env.example` is safe to commit.

Docker Compose reads these values from `.env`. Use `mock` for deterministic local testing or `groq` for generated answers:

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

In a second terminal, run the Streamlit frontend:

```powershell
streamlit run frontend/streamlit_app.py
```

Open `http://127.0.0.1:8501`. The local frontend defaults to `http://127.0.0.1:8000`; override it with `API_URL` when needed.

If the PDFs change, rebuild the RAG index:

```powershell
python scripts/ingest_documents.py
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
docker compose build --no-cache
docker compose up -d
```

Check the container:

```powershell
docker compose ps
```

Stop:

```powershell
docker compose down
```

The API is available at `http://127.0.0.1:8000` and Streamlit at `http://127.0.0.1:8501`. Inside Compose, Streamlit reaches the API through `http://app:8000`.

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

RAG responses expose the document filename, page number, and a short relevant excerpt. Full retrieved text is used internally for grounding but is not returned as API evidence.

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
   "evidence": [
      {
         "source": "rag",
         "document": "inventory_policy.pdf",
         "page": 1,
         "excerpt": "...reorder threshold..."
      }
   ],
   "verification": {"ok": true, "attempts": 1},
   "errors": [],
   "latency": {}
}
```

Unsupported forecasting questions are refused because the agent does not contain a forecasting model. Empty queries return HTTP `422`.

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
| RAG evaluation | **85% Hit@1 / 100% Hit@3** |

## Design Goals

- Evidence-grounded answers
- Clear separation of planning, tools, generation, and verification
- CPU-friendly deployment
- Containerized execution
- Testable components
- Easy LLM provider replacement

## Deployment

Render deployments use the same repository and `main` branch. Deploy the backend and Streamlit services after changes. Configure the Streamlit service with:

```env
API_URL=https://your-api-service.onrender.com
```

The frontend uses `http://127.0.0.1:8000` locally, `http://app:8000` in Docker Compose, and the configured `API_URL` on Render.

