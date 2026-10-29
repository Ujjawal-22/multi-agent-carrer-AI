# Phase 4 Setup — RAG

Adds a retrieval subsystem grounding the Recommendation and Interview Prep
agents in a curated knowledge base, instead of relying purely on the LLM's
own training knowledge.

## Design recap

- **Knowledge base scope (v1)**: skill/technology reference docs,
  interview question patterns, and general role-requirement context — 13
  hand-authored markdown files under `data/knowledge_base/`.
- **Embeddings**: Gemini's `gemini-embedding-2` model (not a local model —
  keeps the heavy `torch`/`sentence-transformers` stack off your machine,
  consistent with the hardware-constraint decisions made back in Phase 0).
- **Retrieval**: hybrid — dense (Qdrant) + keyword (BM25 via `rank-bm25`,
  pure Python) — combined via reciprocal rank fusion.
- **No reranking** — deliberately skipped given the knowledge base's small
  size and your hardware constraints. Easy to add later in
  `app/rag/retriever.py` if quality ever needs it.
- **Role-requirement docs are explicitly labeled as general industry
  context** in both agents' prompts — never used to invent gaps beyond
  what `skill_gap_result` already detected.

## 1. Install new dependencies

```powershell
pip install -r requirements.txt
```

Adds `qdrant-client`, `rank-bm25`, `langchain-text-splitters`.

## 2. Confirm Qdrant is running

```powershell
docker compose up -d qdrant
docker ps
```

Should show `career_ai_qdrant` as `Up` (it's been running unused since
Phase 1 — this is the first phase that actually uses it).

## 3. Run the ingestion script

This populates Qdrant with embedded chunks from the knowledge base. It's
a standalone script, not an API endpoint — rerun it whenever you add or
change knowledge base content.

```powershell
cd backend
python -m app.rag.ingest
```

You should see log output chunking each file and embedding/upserting in
batches, ending with "Ingestion complete: N chunks indexed."

## 4. Run tests

```powershell
pytest
```

New test files: `test_chunking.py`, `test_knowledge_base.py` (includes a
test that directly verifies chunk IDs are deterministic across reloads —
this is the property hybrid fusion depends on), and `test_retriever.py`
(mocks the embedding API and Qdrant search, uses the real knowledge base
content for BM25).

## 5. Verify the health check

```
http://localhost:8000/api/health
```

Should now show `"qdrant": "ok"` alongside `"database": "ok"`.

## 6. Run a real analysis and check the RAG grounding

This is the main thing to verify: do Recommendation and Interview Prep
actually read better / more specifically now?

In the response, check:
- `recommendation_sources` and `interview_sources` — should list which
  knowledge base files were actually used (e.g. `langchain.md`,
  `genai_engineer.md`). If these are empty, retrieval found nothing
  relevant or isn't running — check Qdrant is up and ingestion succeeded.
- `recommendation_result` — do the certification suggestions and
  technology explanations read more specific/accurate than before Phase
  4? Does anything in the "general industry context" section leak through
  as a false claim about a specific gap not in `skill_gap_result`? (It
  shouldn't — the prompt explicitly forbids this.)
- `interview_result.questions` — do any questions now show noticeably
  more technical precision (e.g. referencing a specific RAG/LangGraph
  concept accurately) compared to the pre-Phase-4 version?

**Known limitation, documented not hidden**: `recommendation_sources` and
`interview_sources` are only returned on the `POST /api/analysis`
response right now, not yet persisted to the database — `GET
/api/analysis/{id}` will return empty lists for these two fields until a
follow-up slice adds that persistence. The actual recommendation/interview
content itself IS fully persisted either way.

## Troubleshooting

**Ingestion fails with a Qdrant connection error:**
Confirm the qdrant container is actually running (`docker ps`) and
`QDRANT_URL` in `.env` matches (`http://localhost:6333` by default).

**`recommendation_sources`/`interview_sources` are empty:**
Either ingestion wasn't run, or Qdrant was down when the analysis ran
(check backend logs — retrieval degrades gracefully to BM25-only or even
empty results rather than failing the whole agent, by design).

**Embedding calls seem slow or rate-limited:**
Check aistudio.google.com/rate-limit for `gemini-embedding-2` specifically
— it may have a different quota tier than your chat model.
