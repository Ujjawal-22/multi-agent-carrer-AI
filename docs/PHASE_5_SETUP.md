# Phase 5 Setup — Frontend (Part 1: Backend Streaming Progress)

Before any frontend code, this part converts `POST /api/analysis` from a
long-blocking synchronous call into an immediately-returning background
task with genuine, real per-node progress — not a simulated progress bar.

## What changed

- `Analysis.current_step` (new nullable column) — a human-readable label
  like `"Analyzing resume + Analyzing job description"`, updated live as
  the LangGraph pipeline streams through each node via
  `graph.stream(..., stream_mode="values")` instead of `graph.invoke()`.
- `POST /api/analysis` now returns **`202 Accepted`** immediately with
  `status: "pending"`, and queues the actual pipeline execution as a
  FastAPI `BackgroundTasks` job.
- `GET /api/analysis/{id}` now also returns `current_step`. **Important
  scope note**: the step label updates live during the run, but the
  actual structured results (resume_extraction, skill_gap_result, etc.)
  are still only persisted once the ENTIRE pipeline finishes — so while
  `status` is `"pending"` or `"running"`, expect `current_step` to be
  populated but every result field to still be `null`. This was a
  deliberate scope choice: live step labels give real progress feedback
  without requiring a larger refactor to incrementally persist each
  agent's structured output mid-run.

## 1. Run the new migration

```powershell
alembic upgrade head
```

Creates migration `0008` (adds `current_step` to `analyses`).

## 2. Run tests

```powershell
pytest
```

No test changes needed for this part — the existing orchestrator tests
already cover the LangGraph pipeline logic directly (via `build_analysis_graph()`),
independent of how the API route invokes it. The route's background-task
wiring itself isn't covered by an automated test yet, since properly
testing `BackgroundTasks` without triggering real DB/API calls needs a
more involved test setup (mocked DB session + mocked LLM providers) —
flagged as a reasonable Phase 9 (Testing) task rather than retrofitted
here. Manual verification (next step) is how we're validating this for
now, consistent with how every other slice's real behavior has been
checked.

## 3. Manually verify the new async behavior via Swagger

1. Restart the backend: `uvicorn app.main:app --reload`
2. `POST /api/analysis` with a real `resume_id`/`job_description_id` —
   this should now return **instantly** (not 30-60 seconds later) with
   `202` and `status: "pending"`.
3. Immediately start polling `GET /api/analysis/{id}` every couple of
   seconds. You should see `current_step` change across calls — something
   like:
   - `"Starting analysis"`
   - `"Analyzing resume + Analyzing job description"` (both complete
     around the same time, since they run in parallel)
   - `"Computing skill gap"`
   - `"Running ATS analysis + Analyzing experience & projects"` (parallel
     pair again)
   - `"Calculating match score"`
   - `"Generating recommendations + Generating interview questions"`
     (final parallel pair)
   - `"Completed"`
4. Once `status` is `"completed"`, all the structured result fields
   should be populated exactly as before — this part doesn't change what
   gets computed, only how progress is reported while it's running.

**This is the part most worth actually watching happen** — it's a
genuine, real demonstration of LangGraph's streaming capability, not
something to just trust works from reading the code.

## What's next (Part 2)

The actual React frontend: Vite + TypeScript + Tailwind, polling this new
endpoint via TanStack Query, with a live progress stepper UI built
directly from the real `current_step` values above.
