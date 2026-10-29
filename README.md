# Multi-Agent Job & Resume Intelligence System

> **Status: Phase 4 (RAG) core complete.** All 8 agent graph nodes
> (Phase 3) are built and verified; Recommendation and Interview Prep now
> ground their output in a curated, retrieved knowledge base instead of
> relying purely on LLM training knowledge. Resume Optimization (optional,
> user-triggered) remains a separate Phase 6 feature.

## Project Overview

A multi-agent Generative AI application that analyzes a candidate's resume
against a job description and produces an explainable career analysis:
skill-gap breakdown, ATS compatibility, experience/project relevance, an
overall match score, personalized recommendations grounded in retrieved
reference material, interview questions, and (Phase 6) optional resume
optimization.

Built as a portfolio project demonstrating production-oriented GenAI
engineering: multi-agent orchestration (LangGraph), retrieval-augmented
generation (Qdrant hybrid search), structured LLM outputs, observability
(Langfuse, Phase 8), and a real evaluation methodology (Phase 7) — not
just "call an LLM API."

## Architecture (current)

```
React Frontend (Phase 5) → FastAPI Backend → LangGraph Orchestrator

START --> resume_analyzer --\
START --> jd_analyzer -------> skill_gap --> ats_analysis ---------\
                                          \-> experience_analysis --> matching --> recommendation --------\
                                                                                \-> interview_prep --------> END
                                                                                        |            |
                                                                                        v            v
                                                                            [RAG: Qdrant + BM25 hybrid retrieval]

PostgreSQL (every agent's result, as JSONB)
```

Three genuine parallel fan-outs: Resume+JD (from START), ATS+Experience
(from skill_gap), Recommendation+Interview Prep (from matching).
**Matching** computes its score deterministically (zero LLM calls — see
`app/services/matching_scorer.py`), with one LLM call only for a
narrative explanation of its own already-computed numbers.

**Recommendation and Interview Prep** (Phase 4) now retrieve relevant
chunks from a curated knowledge base — skill/technology reference docs,
interview question patterns, and general role-requirement context — via
hybrid (dense + keyword) search, before generating their output. Retrieved
role-requirement context is explicitly labeled in-prompt as *general
industry context*, never usable to invent a gap beyond what
`skill_gap_result` already detected.

## Tech Stack

- **Backend:** Python, FastAPI, Pydantic, SQLAlchemy, Alembic
- **Agents/Orchestration:** LangGraph
- **LLM Provider:** Google Gemini (`gemini-2.5-flash-lite`) via the
  `google-genai` SDK, abstracted behind `LLMProvider`
- **Embeddings:** Gemini (`gemini-embedding-2`) — chosen over a local
  model specifically to avoid the heavy `torch`/`sentence-transformers`
  dependency stack on constrained hardware (16GB RAM, no GPU)
- **Vector DB:** Qdrant
- **Hybrid retrieval:** Qdrant (dense) + `rank-bm25` (keyword), fused via
  reciprocal rank fusion — no reranking stage (deliberately skipped;
  see Phase 4 design notes)
- **Database:** PostgreSQL
- **Document processing:** PyMuPDF (PDF), python-docx (DOCX), Tesseract
  OCR (scanned PDF fallback)
- **Frontend:** React, TypeScript, Tailwind CSS (Phase 5)
- **Observability:** Langfuse (Phase 8)
- **Deployment:** Docker, Docker Compose

## Local Development Setup

Follow these in order:
1. [`docs/PHASE_1_SETUP.md`](docs/PHASE_1_SETUP.md)
2. [`docs/PHASE_2_SETUP.md`](docs/PHASE_2_SETUP.md)
3. [`docs/PHASE_3_SETUP.md`](docs/PHASE_3_SETUP.md)
4. [`docs/PHASE_4_SETUP.md`](docs/PHASE_4_SETUP.md) — Qdrant ingestion,
   hybrid retrieval, RAG-grounded agent verification

## Project Structure

```
multi-agent-career-ai/
├── backend/
│   ├── app/
│   │   ├── agents/         # 8 LangGraph nodes + orchestrator + prompts/
│   │   ├── api/routes/     # health, resumes, jobs, analysis
│   │   ├── core/           # config, logging, exceptions
│   │   ├── db/             # SQLAlchemy engine/session/base
│   │   ├── models/         # ORM models (one result table per agent)
│   │   ├── rag/            # chunking, embeddings, vector_store, retriever,
│   │   │                   # ingest.py (standalone script), knowledge_base.py
│   │   ├── schemas/        # Pydantic request/response + agent I/O contracts
│   │   ├── services/       # document processing, llm/ provider abstraction,
│   │   │                   # matching_scorer.py (deterministic scoring)
│   │   ├── evaluation/     # Phase 7: eval scripts
│   │   └── main.py
│   ├── tests/
│   ├── migrations/         # Alembic migrations (0001-0007)
│   └── requirements.txt
├── frontend/                # Phase 5
├── data/
│   ├── resumes/               # git-ignored content
│   ├── job_descriptions/      # git-ignored content
│   └── knowledge_base/        # RAG source content (committed - it's
│       ├── skills/             # reference material, not PII)
│       ├── interview_questions/
│       └── role_requirements/
├── evaluation/               # eval datasets + results (Phase 7)
├── docker/
├── docs/
├── .env.example
├── docker-compose.yml
└── README.md
```

## Development Phases

- [x] Phase 0 — Architecture design
- [x] Phase 1 — Foundation
- [x] Phase 2 — Document processing
- [x] Phase 3 — Agent system (all 8 nodes)
- [x] Phase 4 — RAG (hybrid retrieval, grounding Recommendation + Interview
      Prep; reranking explicitly deferred, resume_sources DB persistence
      explicitly deferred — see Limitations)
- [ ] Phase 5 — Frontend ← **next**
- [ ] Phase 6 — Resume optimization (optional, user-triggered)
- [ ] Phase 7 — Evaluation
- [ ] Phase 8 — Observability
- [ ] Phase 9 — Testing
- [ ] Phase 10 — Deployment

## Key Engineering Decisions (with rationale)

- **Synchronous SQLAlchemy, not async** — the real bottleneck is LLM call
  latency, not database I/O.
- **LLM provider abstraction from day one** — agents depend on
  `LLMProvider`, never a specific SDK.
- **Gemini's `response_schema` rejects Pydantic default values** — every
  Gemini-facing schema uses required fields only (discovered via a real
  `ValueError` during development).
- **Not every "agent" needs an LLM call** — Matching's score is a
  deterministic weighted formula; only its narrative is LLM-generated.
- **Gemini embeddings over a local model** — avoids `torch`/
  `sentence-transformers` on hardware that can't comfortably run them;
  the same reasoning that pushed local LLM inference to a cloud API back
  in Phase 0 applies equally to embeddings.
- **Hybrid retrieval without reranking** — a cross-encoder reranker needs
  the same heavy dependency stack just avoided for embeddings, and a
  small curated knowledge base (tens of documents) doesn't clearly need
  it. Documented as a explicit scope decision, not a silent omission —
  easy to add later if retrieval quality ever demands it.
- **Role-requirement RAG context is explicitly labeled as general
  industry context, in-prompt** — prevents the exact fabrication risk RAG
  could otherwise introduce: using generic "what a GenAI Engineer
  typically needs" reference material to invent a gap the specific JD
  never actually required.
- **Shared chunk-ID generation between ingestion and retrieval** — both
  paths route through one function (`app/rag/knowledge_base.py`)
  specifically to guarantee dense (Qdrant) and BM25 results for the same
  underlying chunk are recognized as the same chunk during fusion — a bug
  class caught and eliminated by design, not by testing after the fact.
- **`.get(key, default)` for all LangGraph state reads** — a field only
  exists once some node actually returns it during that run.

## Limitations (living section)

- **Reranking is not implemented** — hybrid (dense + BM25) retrieval only,
  by deliberate choice given hardware constraints and a small knowledge
  base. Worth revisiting if retrieval precision ever becomes a measured
  problem in Phase 7's evaluation.
- **`recommendation_sources`/`interview_sources` are only returned on the
  `POST /api/analysis` response, not yet persisted to the database** —
  `GET /api/analysis/{id}` returns empty lists for these two fields for
  now. The actual recommendation/interview content is fully persisted
  either way; only the source-attribution metadata isn't yet.
- **Knowledge base is intentionally narrow (v1 scope)**: skill/tech
  reference docs, an interview question bank, and role-requirement
  context for a handful of common role archetypes — not resume
  best-practice docs (deferred to Phase 6) or a broad library of real job
  descriptions.
- `education_match` and `domain_match` in the Matching Agent use shallow
  keyword-overlap heuristics — documented as the weakest, lowest-weighted
  sub-scores.
- The ATS score is explicitly an LLM-based heuristic estimate, stated
  directly in every response via `ats_result.methodology_note`.
- No overstated claims about match-score validity or evaluation results
  not backed by actual experiments (Phase 7 will add real measured
  metrics).
