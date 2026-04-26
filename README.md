# DocuMind

DocuMind is a local-first AI document intelligence application for uploading documents and asking grounded questions over their contents. It uses a Retrieval-Augmented Generation (RAG) pipeline to extract text, chunk documents, index embeddings, retrieve relevant evidence, and answer with citations instead of relying on open-ended model memory.

The current product includes:

- a FastAPI backend for ingestion, indexing, retrieval, and chat
- a polished Next.js frontend in `web/`
- local generation through Ollama
- sentence-transformers embeddings
- FAISS vector search
- multi-document upload and removal
- grounded answers with fallback behavior

## What the product does

DocuMind lets a user:

- upload PDF, DOCX, and TXT files
- automatically ingest and index them
- search relevant chunks across one or more documents
- ask grounded questions over the active document set
- inspect citations for each answer
- remove one document or clear the workspace entirely

If the retrieved context is weak, the system returns a fallback response instead of hallucinating.

## Current stack

### Backend

- Python
- FastAPI
- Pydantic
- structlog

### AI and retrieval

- sentence-transformers for embeddings
- Ollama for local generation
- `qwen2.5:7b-instruct` as the default local model
- FAISS for vector search
- hybrid dense + lexical retrieval

### Frontend

- Next.js App Router
- TypeScript
- Tailwind CSS
- Framer Motion
- Zustand
- TanStack Query

### Testing

- pytest
- Vitest

## Architecture overview

```text
Next.js Frontend (web/)
  - landing page
  - workspace UI
  - upload flow
  - grounded chat
  - citations and document management
        |
        v
FastAPI Backend (app/)
  - /documents/upload
  - /documents/index
  - /documents/search
  - /documents/{document_id}
  - /documents/reset
  - /chat/query
  - /system/status
        |
        v
Core Services
  - ingestion: parse PDF/DOCX/TXT, normalize text, persist uploads
  - chunking: fixed and recursive chunking strategies
  - embeddings: pluggable embedding provider
  - vector store: FAISS-backed local index
  - retrieval: dense + lexical ranking, optional reranking
  - generation: grounded answer generation with fallback behavior
  - chat: session-aware orchestration and confidence scoring
        |
        v
Local Runtime State
  - uploaded files
  - FAISS index files
  - chunk metadata
  - evaluation logs
```

## Project layout

```text
DocuMind/
  app/
    main.py
    routes/
    services/
    models/
    utils/
  web/
    src/
  data/
  tests/
  .env.example
  Dockerfile
  requirements.txt
  README.md
```

## How it works

1. The user uploads one or more documents from the web workspace.
2. The backend extracts and normalizes text from PDF, DOCX, or TXT files.
3. The text is chunked using the selected strategy and overlap settings.
4. Chunk embeddings are generated and stored in a FAISS index.
5. When the user asks a question, DocuMind retrieves the most relevant chunks.
6. The answer layer responds only from retrieved context and returns citations.
7. If context is insufficient, the system falls back instead of generating a weak answer.

## Features

- multi-format ingestion: PDF, DOCX, TXT
- fixed and recursive chunking
- local vector search with FAISS
- grounded chat with citations
- session-aware conversation flow
- multi-document retrieval
- per-document removal
- clear workspace reset
- local-first model execution with Ollama
- structured logging and deterministic tests

## Local setup

### Prerequisites

- Python 3.11
- Node.js 18+ and npm
- Ollama installed locally

### 1. Install backend dependencies

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### 2. Create backend environment file

```powershell
Copy-Item .env.example .env
```

The default configuration is designed for local usage. The important defaults are:

- `LLM_PROVIDER=ollama`
- `OLLAMA_MODEL=qwen2.5:7b-instruct`
- `EMBEDDING_PROVIDER=sentence-transformers`
- `VECTOR_STORE_PROVIDER=faiss`
- `RERANKER_PROVIDER=none`

### 3. Pull the local model

```powershell
ollama pull qwen2.5:7b-instruct
```

### 4. Start the backend

```powershell
.\run_backend.ps1
```

Or directly:

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

The backend will be available at `http://127.0.0.1:8000`.

### 5. Install frontend dependencies

```powershell
Set-Location web
npm install
```

### 6. Create frontend environment file

Create `web/.env.local` with:

```text
DOCUMIND_API_URL=http://127.0.0.1:8000
```

### 7. Start the frontend

```powershell
.\run_frontend.ps1
```

Or directly from `web/`:

```powershell
npm run dev
```

The frontend will be available at `http://127.0.0.1:3000`.

## Running with Docker

The provided Dockerfile packages the backend service.

Build:

```powershell
docker build -t documind .
```

Run:

```powershell
docker run --rm -p 8000:8000 --env-file .env documind
```

The frontend remains a separate Next.js process in this repository.

## Environment variables

Important backend settings from `.env.example`:

| Variable | Purpose | Default |
|---|---|---|
| `APP_NAME` | Application name | `DocuMind` |
| `APP_ENV` | Environment name | `development` |
| `APP_HOST` | Backend host | `0.0.0.0` |
| `APP_PORT` | Backend port | `8000` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `DOCUMIND_API_URL` | Backend URL used by the frontend | `http://127.0.0.1:8000` |
| `LLM_PROVIDER` | Generation provider | `ollama` |
| `OLLAMA_BASE_URL` | Ollama server URL | `http://127.0.0.1:11434` |
| `OLLAMA_MODEL` | Local generation model | `qwen2.5:7b-instruct` |
| `EMBEDDING_PROVIDER` | Embedding provider | `sentence-transformers` |
| `EMBEDDING_MODEL` | Embedding model | `sentence-transformers/all-MiniLM-L6-v2` |
| `RERANKER_PROVIDER` | Reranker provider | `none` |
| `VECTOR_STORE_PROVIDER` | Vector database backend | `faiss` |
| `DEFAULT_TOP_K` | Default retrieval depth | `5` |
| `DEFAULT_CHUNK_SIZE` | Default chunk size | `800` |
| `DEFAULT_CHUNK_OVERLAP` | Default chunk overlap | `120` |
| `MINIMUM_GROUNDING_SCORE` | Fallback gating threshold | `0.2` |

## API overview

### Health and status

- `GET /api/v1/health`
- `GET /api/v1/system/status`

### Documents

- `POST /api/v1/documents/upload`
  - upload one or more `.pdf`, `.docx`, or `.txt` files
- `POST /api/v1/documents/index`
  - index all or selected documents
- `POST /api/v1/documents/search`
  - retrieve top-k matching chunks
- `DELETE /api/v1/documents/{document_id}`
  - remove one document and refresh the index
- `POST /api/v1/documents/reset`
  - clear all documents, index state, and sessions

### Chat

- `POST /api/v1/chat/query`
  - accepts `session_id`, `user_query`, and optional `top_k`
  - returns answer, confidence score, citations, and retrieved chunk metadata

## Testing

### Backend

```powershell
python -m pytest -q
```

### Frontend

```powershell
Set-Location web
npm test
```

The test suite covers:

- ingestion for PDF, DOCX, and TXT
- chunking behavior
- indexing and retrieval
- grounded chat and fallback logic
- upload and document removal routes
- frontend API helper behavior
- frontend file-selection behavior

## Logging

DocuMind uses structured logging on the backend and log files for local runs.

Important runtime events include:

- document uploads
- indexing operations
- retrieval queries
- chat requests
- fallback responses
- document removal
- workspace resets

## Design decisions

- Local-first by default so the product is easy to run and demo on one machine
- Pluggable AI components so embeddings, LLM, and reranking can be swapped later
- Grounding-first answer strategy instead of optimistic generation
- Simplified workspace UX focused on user value rather than internal state
- Conservative fallback behavior to reduce hallucinations

## Current limitations

- summary generation was intentionally removed from the workspace because the local quality was not reliable enough
- runtime state is primarily local and in-memory rather than multi-user persistent storage
- removing one document triggers reindexing of the remaining document set
- the backend Dockerfile does not package the Next.js frontend

## Future improvements

- stronger summarization with better chunk selection and prompting
- persistent multi-user storage
- richer retrieval evaluation and benchmarking
- improved reranking with a lighter local model
- background indexing for larger uploads

## Why this project is useful in a portfolio

DocuMind is more than a toy RAG demo. It shows:

- full-stack product execution
- backend API design
- document ingestion and retrieval engineering
- local AI model integration
- production-minded fallback behavior
- frontend product polish
- testing and operational hardening

