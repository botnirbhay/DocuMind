# DocuMind

DocuMind is a local-first AI application for chatting with your documents using retrieval-augmented generation. Users can upload PDFs, DOCX files, and text files, build a vector index over extracted chunks, search relevant passages, and ask grounded questions that return citations and confidence signals.

The repository is structured like a small production SaaS codebase rather than a one-off demo. It includes a FastAPI backend, a Streamlit frontend, deterministic tests, structured logging, Docker packaging, and modular service boundaries for ingestion, chunking, embeddings, retrieval, and answer generation.

## Why This Project Is Strong

- It solves a real document QA workflow end to end instead of stopping at isolated RAG components.
- The system is grounded by design: retrieval, answer generation, citations, confidence, and fallback behavior are all implemented and tested together.
- The codebase is modular enough to swap providers later without rewriting route handlers or UI flows.
- The repo is demo-ready: Docker support, local setup, structured logging, deterministic tests, and a polished frontend are already in place.

## What DocuMind Does

- Upload PDF, DOCX, and TXT documents
- Extract and normalize document text
- Chunk text with fixed or recursive strategies
- Generate embeddings and index chunks with FAISS
- Search indexed chunks with similarity retrieval
- Answer questions only from retrieved context
- Return citations with document metadata and chunk snippets
- Maintain session-aware chat history in the frontend and backend
- Expose a clean API plus a polished Streamlit interface

## Architecture Overview

```text
Streamlit Frontend
  - upload workflow
  - indexing controls
  - retrieval preview
  - grounded chat UI
        |
        v
FastAPI Backend
  - /documents/upload
  - /documents/index
  - /documents/search
  - /chat/query
        |
        v
Services
  - ingestion: parse PDF/DOCX/TXT, normalize text, store metadata
  - chunking: fixed and recursive chunk strategies
  - embeddings: pluggable embedding providers
  - vector store: FAISS-backed local index
  - retrieval: search top-k relevant chunks
  - generator: grounded extractive answer generation
  - chat: session-aware orchestration and fallback behavior
        |
        v
Local Storage
  - uploaded source files
  - FAISS index files
  - chunk metadata
  - evaluation/log directories
```

## Project Layout

```text
DocuMind/
  app/
    main.py
    routes/
    services/
    models/
    utils/
  frontend/
    app.py
    services/
    utils/
  data/
  tests/
  .env.example
  Dockerfile
  requirements.txt
  README.md
```

## Setup

### Prerequisites

- Python 3.11
- `pip`

### 1. Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Defaults are sensible for local development. The app works without external APIs when `LLM_PROVIDER=extractive` and `EMBEDDING_PROVIDER=hash`. `sentence-transformers` is still supported, but it depends on a working local PyTorch stack.

### 3. Run the backend

```bash
uvicorn app.main:app --reload
```

The API will start on `http://127.0.0.1:8000` by default.

### 4. Run the frontend

In a second terminal:

```bash
streamlit run frontend/app.py
```

The Streamlit UI uses `DOCUMIND_API_URL` to find the backend. The default is `http://127.0.0.1:8000`.

## Docker

The Docker image runs the FastAPI backend.

Build:

```bash
docker build -t documind .
```

Run:

```bash
docker run --rm -p 8000:8000 --env-file .env documind
```

Health check:

- `GET /api/v1/health`

The frontend is still intended to run as a separate local process in this repository.

## Environment Variables

Key settings from `.env.example`:

| Variable | Purpose | Default |
|---|---|---|
| `APP_NAME` | API application name | `DocuMind` |
| `APP_ENV` | Environment label | `development` |
| `APP_HOST` | API host binding | `0.0.0.0` |
| `APP_PORT` | API port | `8000` |
| `LOG_LEVEL` | Logging verbosity | `INFO` |
| `REQUEST_LOG_ENABLED` | Enable request logs | `true` |
| `DOCUMIND_API_URL` | Frontend backend URL | `http://127.0.0.1:8000` |
| `LLM_PROVIDER` | Answer generation provider | `extractive` |
| `EMBEDDING_PROVIDER` | Embedding backend | `hash` |
| `EMBEDDING_MODEL` | Sentence transformer model | `sentence-transformers/all-MiniLM-L6-v2` |
| `VECTOR_STORE_PROVIDER` | Vector storage backend | `faiss` |
| `DATA_DIR` | Root local data directory | `./data` |
| `UPLOAD_DIR` | Uploaded file storage | `./data/uploads` |
| `VECTOR_INDEX_DIR` | FAISS index storage | `./data/vector_index` |
| `EVAL_LOG_PATH` | Evaluation log output path | `./data/logs/evaluations.jsonl` |
| `DEFAULT_TOP_K` | Default retrieval depth | `5` |
| `DEFAULT_CHUNK_SIZE` | Default chunk size | `800` |
| `DEFAULT_CHUNK_OVERLAP` | Default overlap | `120` |
| `MINIMUM_GROUNDING_SCORE` | Minimum confidence gate for grounded answers | `0.2` |

## API Overview

### Health and status

- `GET /api/v1/health`
- `GET /api/v1/system/status`

### Documents

- `POST /api/v1/documents/upload`
  - multipart upload of one or more `.pdf`, `.docx`, `.txt` files
- `POST /api/v1/documents/index`
  - builds the vector index for all or selected documents
- `POST /api/v1/documents/search`
  - returns top-k matching chunks and metadata

### Chat

- `POST /api/v1/chat/query`
  - accepts `session_id`, `user_query`, and optional `top_k`
  - returns `answer`, `citations`, `confidence_score`, and retrieved chunk metadata

## Testing

Run the full suite:

```bash
python -m pytest -q
```

The tests cover:

- file extraction for PDF, DOCX, and TXT
- chunking behavior
- indexing and retrieval
- grounded chat behavior and fallback handling
- frontend API client and session helpers
- end-to-end upload -> index -> search/chat integration flows

Tests are deterministic and do not depend on external network calls.

## Logging

DocuMind uses structured JSON logging via `structlog`.

Logged events include:

- app startup and shutdown
- HTTP request completion
- document upload and ingestion completion
- vector index creation
- retrieval queries
- chat queries, confidence, and fallback behavior

This keeps local debugging practical without adding external observability infrastructure.

## Design Decisions

- **Local-first execution:** the default stack works on a laptop without managed infrastructure.
- **Pluggable service boundaries:** embeddings, retrieval, and answer generation are isolated behind service interfaces.
- **Grounding-first answers:** chat responses are derived from retrieved context and fall back cleanly when evidence is weak.
- **Deterministic tests:** the suite uses mocked or local providers to avoid live API dependencies.
- **Streamlit for operator UX:** the frontend is optimized for local workflows and portfolio-quality presentation rather than multi-tenant deployment.

## Limitations

- The default answer generator is extractive rather than full generative synthesis.
- Session memory is stored in process memory, not durable storage.
- FAISS indexing is local-only and not designed for concurrent multi-user workloads.
- The frontend assumes a separately running backend service.
- Evaluation logging exists as local file output, not a full analytics pipeline.

## Future Improvements

- Swap in OpenAI or another hosted LLM provider behind the existing generator interface
- Add persistent conversation storage
- Support background indexing jobs for large uploads
- Add auth, quotas, and multi-user separation
- Export retrieval and answer traces into a richer evaluation dashboard

## Quick Start Command Sequence

Suggested demo flow:

1. Start the FastAPI backend.
2. Start the Streamlit frontend.
3. Upload two or three small documents.
4. Build the index.
5. Run a retrieval preview query.
6. Ask a grounded question and expand the citations panel.

Backend:

```bash
uvicorn app.main:app --reload
```

Frontend:

```bash
streamlit run frontend/app.py
```

Tests:

```bash
python -m pytest -q
```
