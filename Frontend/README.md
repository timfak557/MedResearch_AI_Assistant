# MedResearch AI — Frontend

Professional React frontend for the MedResearch AI backend: an evidence-grounded
medical research assistant over the MedQuAD knowledge base.

Built with React 18, TypeScript (strict), Vite, Tailwind CSS, shadcn-style UI
components, Lucide icons, React Router, TanStack Query, React Markdown,
Zod + React Hook Form.

## Features

Chat with markdown answers and interactive `[1]` citations that open the matching
evidence card · evidence panel with relevance scores and NIH source links ·
knowledge search with source/question-type filters · research history (device-local,
can be disabled in Settings) · saved sources · light/dark/system theme ·
system status (API, Qdrant, embedding model, LLM) · safety notices per category ·
insufficient-context state · retrieval-confidence display with honest labeling ·
responsive layout (desktop three-pane → mobile drawer + bottom evidence sheet) ·
accessible (ARIA labels, keyboard nav, focus rings, reduced-motion support).

## Run

Requires Node 18+. The FastAPI backend must be running (default `http://localhost:8080`).

```bash
npm install
cp .env.example .env    # adjust VITE_API_BASE_URL if your backend uses another port
npm run dev             # http://localhost:5173
```

Other commands:

```bash
npm run build     # type-check + production build (dist/)
npm run preview   # serve the production build locally
npm run test      # Vitest + React Testing Library
npm run lint      # ESLint
```

## Docker

```bash
docker build -t medresearch-frontend --build-arg VITE_API_BASE_URL=http://localhost:8080 .
docker run -p 3000:80 medresearch-frontend
```

Multi-stage build; assets served by nginx with SPA routing and immutable asset
caching. No secrets are ever baked into the image — `VITE_` variables are public
by design, so only the backend URL belongs there.

## Architecture rules

The frontend never talks to Qdrant or the LLM directly, never stores API keys,
and never makes medical-safety decisions — all of that lives in the backend.
This app is UI, state, validation, accessibility, and REST calls only
(`src/api/` is the single integration surface; `src/types/` mirrors the backend
schemas with all optional fields handled defensively).
