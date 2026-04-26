# DocuMind Web

This is the premium Next.js frontend for DocuMind. It connects to the existing FastAPI backend and provides:

- a landing page
- a product workspace
- document upload and indexing
- retrieval preview
- grounded chat with citations

## Stack

- Next.js App Router
- TypeScript
- Tailwind CSS
- Framer Motion
- TanStack Query
- Zustand
- lucide-react

## Environment

Create `web/.env.local`:

```bash
DOCUMIND_API_URL=http://127.0.0.1:8000
```

The browser uses same-origin Next.js route handlers under `/api/v1/*`. Those handlers proxy to the FastAPI backend, so the backend can remain unchanged and you do not need browser-side CORS setup.

## Run locally

From `web/`:

```bash
npm install
npm run dev
```

The app starts on `http://127.0.0.1:3000`.

Make sure the FastAPI backend is already running on `http://127.0.0.1:8000`.

## Test

```bash
npm test
```

## Routes

- `/` landing page
- `/workspace` live product workspace
