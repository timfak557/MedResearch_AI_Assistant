# MedResearch AI Assistant — Backend

An evidence-grounded medical information and research assistant. It answers
medical questions **only** from the [MedQuAD](https://github.com/abachaa/MedQuAD)
dataset (NIH sources), with semantic retrieval over Qdrant, grounded LLM
generation with validated citations, and layered medical safety guardrails.
Exposed as both a FastAPI REST API and an MCP server that share one service layer.

> **Medical disclaimer:** this system provides educational information only.
> It does not diagnose, prescribe, or replace professional medical advice.

## Architecture

```
MedQuAD XML → Downloader → XML Parser → Cleaner → Validator → Dedup
            → Searchable Text → Chunker → Embeddings (all-MiniLM-L6-v2)
            → Qdrant (cosine, payload indexes)

USER → FastAPI / MCP
     → Safety Classification (emergency / self-harm / injection / …)
     → Conversation Query Rewriting  (fresh retrieval every turn)
     → Embedding → Qdrant → Score Filter → Per-record Dedup
     → Optional Reranker (no-op by default; cross-encoder pluggable)
     → Context Builder (budgeted, score-ordered, deduped)
     → RAG Prompt → LLM (OpenAI-compatible, env-configured)
     → Citation Validation (fabricated citations stripped)
     → Output Safety Validation (dosage / diagnosis / leak filters)
     → Response (+ mandatory disclaimer)
```

Layout: `app/core` (config, logging, security, exceptions) · `app/data`
(download → chunk pipeline) · `app/embeddings` · `app/vectorstore` ·
`app/retrieval` · `app/rag` · `app/safety` · `app/services` (search, chat,
conversation — the single business-logic layer) · `app/api` (FastAPI routes) ·
`app/mcp` (MCP server/tools) · `scripts/` · `tests/`.

## Installation

Requires Python 3.11+, Git, and a running Qdrant.

```bash
pip install -r requirements.txt
cp .env.example .env        # then fill in OPENAI_API_KEY etc.
```

### Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `OPENAI_API_KEY` | — | API key for the OpenAI-compatible LLM (never hard-coded) |
| `OPENAI_MODEL` | — | Chat model name (e.g. `gemini-2.5-flash`, `gpt-4o-mini`) |
| `OPENAI_BASE_URL` | — | OpenAI-compatible endpoint (e.g. `https://generativelanguage.googleapis.com/v1beta/openai/`) |
| `EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | Embedding model; a local copy under `models/<name>` is preferred when present |
| `QDRANT_URL` | `http://localhost:6333` | Qdrant endpoint |
| `QDRANT_API_KEY` | empty | Qdrant API key (cloud deployments) |
| `QDRANT_COLLECTION` | `medquad_documents` | Collection name |
| `TOP_K` / `FINAL_CONTEXT_K` | 10 / 5 | Candidates retrieved / kept |
| `MIN_RELEVANCE_SCORE` | 0.45 | Cosine score threshold |
| `CHUNK_SIZE` / `CHUNK_OVERLAP` | 1000 / 150 | Chunking parameters (chars) |
| `MAX_QUERY_LENGTH` / `MAX_TOP_K` | 2000 / 20 | Input limits |
| `CONVERSATION_MAX_TURNS` | 10 | History window per conversation |
| `LOG_LEVEL` / `ENVIRONMENT` | INFO / development | `production` switches to JSON logs |

## Data pipeline

```bash
python scripts/download_medquad.py        # git-clones MedQuAD (11,274 XML files)
python scripts/explore_medquad.py         # read-only stats → exploration_report.json
python scripts/prepare_medquad.py         # parse→clean→validate→dedup→chunk → JSONL
python scripts/ingest_medquad.py          # embed + upsert into Qdrant
```

`ingest_medquad.py` flags: `--input`, `--batch-size`, `--limit`, `--dry-run`,
and `--recreate` (the only way an existing collection is ever deleted).
Outputs: `processing_report.json` and `ingestion_manifest.json` (dataset hash,
model, vector dimension, counts, timestamp). The whole pipeline is repeatable
and idempotent — deterministic chunk IDs mean re-ingestion never duplicates.

Dataset note: MedQuAD ships 47,457 QA records, but the answers of the three
MedlinePlus subsets (ADAM, Drugs, Herbs) were removed upstream for copyright
reasons. After validation and exact dedup the usable knowledge base is
**16,375 records → 31,348 chunks**.

### Qdrant setup

Any Qdrant ≥1.15 works. Locally: `docker compose up -d qdrant`, or download a
[release binary](https://github.com/qdrant/qdrant/releases). The collection is
created automatically at ingest time with cosine distance and payload indexes
on `source`, `focus`, `question_type`, `parent_record_id`.

## Running

```bash
uvicorn app.main:app --reload          # API on :8080 (docs at /docs and /redoc)
python -m app.mcp.server               # MCP over stdio (local development)
python -m app.mcp.server --transport streamable-http   # MCP for deployment
docker compose up -d                   # API + Qdrant together
```

## API examples

```bash
curl -s localhost:8080/health
curl -s localhost:8080/ready

curl -s -X POST localhost:8000/api/v1/search \
  -H 'Content-Type: application/json' \
  -d '{"query": "What are the symptoms of diabetes?", "top_k": 5,
       "source": null, "focus": null, "question_type": null}'

curl -s -X POST localhost:8000/api/v1/chat \
  -H 'Content-Type: application/json' \
  -d '{"message": "What are the symptoms of diabetes?", "conversation_id": null}'

curl -s localhost:8080/api/v1/sources
curl -s localhost:8080/api/v1/question-types
curl -s localhost:8080/api/v1/statistics
curl -s -X DELETE localhost:8080/api/v1/conversations/<id>
```

Chat responses include `answer` (with citations `[1]`, `[2]` and the
disclaimer), `sources`, `retrieval_count`, `confidence`,
`insufficient_context`, and `safety_category`.

## MCP tools

`search_medical_knowledge`, `get_medical_record`, `find_related_questions`,
`compare_medical_topics`, `list_medical_sources`, `list_question_types`,
`get_system_statistics` — all thin adapters over the same services the REST
API uses. Logs go to stderr so the stdio JSON-RPC channel stays clean.

## Testing

```bash
pytest tests/unit -q                       # no external dependencies
pytest tests/integration -q -m integration # needs Qdrant + embedding model
```

Integration tests use a dedicated `medquad_test` collection — the production
collection is never touched. LLM calls are always mocked in tests. Covered:
malformed XML, missing answers, duplicates, chunk boundaries, empty/oversized
queries, no-retrieval, fake citations, prompt injection, diagnosis/medication/
emergency requests, LLM failure, Qdrant failure, MCP tool validation.

## Evaluation

```bash
python scripts/evaluate_rag.py --sample 200        # → data/evaluation/results.json
```

Reports Recall@1/5/10, MRR, nDCG@10, retrieval latency (self-retrieval
protocol), insufficient-context accuracy, safety compliance, and — when the
LLM is reachable — citation correctness/completeness and a lexical
faithfulness proxy with unsupported-claim rate.

## Security

- All configuration via environment; secrets held as `SecretStr`, redacted
  from logs by pattern filters; no keys in code or Docker images.
- XML parsed with `defusedxml` — external entities and DTD tricks disabled.
- Input validation everywhere: query length limits, top-K clamping, control
  character stripping, metadata filter sanitization (shared by API and MCP).
- Secure headers, restricted CORS methods, request IDs, sanitized error
  responses (no stack traces), centralized exception handling.
- Prompt injection: classifier blocks injection attempts before RAG; the
  system prompt treats retrieved documents as data, not instructions; output
  is scanned for secret/prompt leakage.
- Rate limiting: deploy behind a reverse proxy (nginx/traefik) or add
  middleware; the request-ID middleware is the integration point.

## Medical safety

- Input classification: emergencies and self-harm short-circuit to support
  messages (no invented phone numbers); prompt injection and off-topic
  requests are declined; diagnosis/treatment/medication questions get general
  information plus a see-a-professional notice — never personal advice.
- Output validation: personalized dosage or stop-medication directives are
  blocked; every answer ends with the medical disclaimer.
- Honesty: when retrieval returns nothing relevant the system says it could
  not find enough information — the LLM is never asked to guess, and previous
  AI answers are never reused as evidence.

## Limitations

- MedQuAD answers date from NIH pages circa 2017-2019 — not current clinical
  guidance, and three MedlinePlus subsets have no answer text.
- The safety classifier is rule-based: fast and auditable, but heuristic.
- Confidence is a retrieval-score heuristic, not a calibrated probability.
- Conversation memory is in-process; use Redis or similar for multi-replica
  deployments.
- English only, matching the dataset.
