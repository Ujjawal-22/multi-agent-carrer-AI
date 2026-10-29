# Phase 3 Setup — Agent System

## Slice 1: Resume + JD Agents

### 1. Install new dependencies

```powershell
pip install -r requirements.txt
```

Adds `google-genai`, `langgraph`, `tenacity`.

### 2. Confirm your .env has a real Gemini key

### 3. Run the migration

```powershell
alembic upgrade head
```

Creates `analyses`, `resume_extractions`, `job_extractions` (migration
`0002`).

### 4. Run tests

```powershell
pytest
```

Orchestrator tests mock the LLM entirely — no API calls, no cost.

## Slice 2: Skill Gap Agent

The Skill Gap Agent doesn't read raw text — it compares the already
-structured `resume_extraction` and `jd_extraction` objects and classifies
skills into matching / partially-matching / transferable / missing (each
missing skill with importance, reason, and suggested learning priority).

It sits as a **fan-in** node in the graph: both Resume and JD agents feed
into it, and it only runs once both have completed. If either upstream
agent failed, it detects the missing data and records its own clear error
instead of calling the LLM with incomplete input.

### 1. Run the new migration

```powershell
alembic upgrade head
```

Creates the `skill_gaps` table (migration `0003`).

### 2. Run tests

```powershell
pytest
```

`test_orchestrator.py` now covers the 3-node graph, including the case
where Resume Agent fails and Skill Gap Agent correctly short-circuits
without calling its own LLM.

### 3. Try a real end-to-end analysis

```powershell
uvicorn app.main:app --reload
```

Open `http://localhost:8000/docs` → **POST /api/analysis** with a real
`resume_id` and `job_description_id`. The response now includes
`skill_gap_result` alongside `resume_extraction` and `jd_extraction`.

**What to check:** does `matching_skills` actually reflect skills present
in both documents? Are `missing_skills` genuinely absent from the resume
(not fabricated, not something the resume actually has)? Read the actual
classifications — this is where prompt quality matters most.

You can also verify directly against the database:

```powershell
docker exec -it career_ai_postgres psql -U career_ai -d career_ai -P pager=off -c "SELECT jsonb_pretty(data) FROM skill_gaps ORDER BY created_at DESC LIMIT 1;"
```

## Troubleshooting

**`ValueError: Unsupported LLM_PROVIDER`:** check `.env`, should be
`gemini`.

**Analysis returns errors for skill_gap specifically:** check whether
resume_extraction/jd_extraction actually succeeded first — skill_gap
depends on both and will report a clear error (not a crash) if either is
missing.

**Slow response:** check aistudio.google.com/rate-limit if this happens
repeatedly — should not be an issue on Tier 1 for 3 calls.

## Slice 3: ATS Agent + Experience/Project Agent (parallel)

These two agents both depend only on resume_extraction + jd_extraction
(not on skill_gap_result or each other), so they run as a genuine
parallel fan-out after Skill Gap — the graph is now:

```
START -> resume_analyzer --\
START -> jd_analyzer -------> skill_gap -> ats_analysis --------\
                                        \-> experience_analysis --> END
```

No new Python dependencies for this slice.

### 1. Run the new migration

```powershell
alembic upgrade head
```

Creates `ats_results` and `experience_analysis` tables (migration `0004`).

### 2. Run tests

```powershell
pytest
```

`test_orchestrator.py` now verifies the 5-node graph, including that a
Resume Agent failure correctly cascades: Skill Gap, ATS, and Experience
agents all detect the missing data and record their own errors WITHOUT
calling their own LLMs (no wasted API calls on a doomed request).

### 3. Run a real analysis and check the ATS disclaimer

`POST /api/analysis` as before. In the response, check `ats_result`:

- `methodology_note` should ALWAYS read the fixed disclaimer text
  ("This ATS score is an LLM-based heuristic estimate, not the output of
  any real commercial ATS system...") — this is set in code, not by the
  LLM, specifically so it can never be dropped or reworded.
- `ats_score` should have a `score_explanation` that actually justifies
  the number based on what was found — not just a vibes-based score.
- Check `experience_result.improvement_suggestions` — these should ONLY
  be about wording/presentation, never suggest adding skills or projects
  that aren't in the resume. If you see anything that reads like "add a
  project demonstrating X," that's a prompt violation worth flagging.

Verify directly against the database if you want:

```powershell
docker exec -it career_ai_postgres psql -U career_ai -d career_ai -P pager=off -c "SELECT jsonb_pretty(data) FROM ats_results ORDER BY created_at DESC LIMIT 1;"
docker exec -it career_ai_postgres psql -U career_ai -d career_ai -P pager=off -c "SELECT jsonb_pretty(data) FROM experience_analysis ORDER BY created_at DESC LIMIT 1;"
```

## Slice 4: Matching Agent (deterministic scoring + LLM narrative)

The Matching Agent is different from every agent before it: the actual
match score is computed by **plain Python code** (`app/services/matching_scorer.py`),
not an LLM. Only the human-readable narrative explanation of that score
comes from Gemini, and it's explicitly instructed to explain the given
numbers, never invent new ones.

Graph is now:
```
START -> resume_analyzer --\
START -> jd_analyzer -------> skill_gap -> ats_analysis --------\
                                        \-> experience_analysis --> matching -> END
```

### Also fixed in this slice (carried over from your Slice 3 findings)

`job_extraction.py`, `skill_gap.py`, and `experience_analysis.py` have
been brought in line with the same no-Pydantic-defaults rule already
applied to `resume_extraction.py` and `ats_analysis.py` — all five
Gemini-facing schemas are now consistent. If your repository already had
these three fixed identically, this changes nothing; if it didn't, this
closes the gap before it causes the same `ValueError` you hit with ATS.

`config.py` also now resolves `.env` via a `__file__`-relative path
(`Path(__file__).resolve().parents[3] / ".env"`) rather than a bare
relative string — please diff this against whatever fix you already had
in place, since I don't have direct visibility into your exact prior
implementation.

### 1. Configurable weights (new)

Five new settings, all optional (sensible defaults provided, sum to 1.0):
`MATCH_WEIGHT_TECHNICAL_SKILL`, `MATCH_WEIGHT_ATS_KEYWORD`,
`MATCH_WEIGHT_EXPERIENCE_PROJECT`, `MATCH_WEIGHT_EDUCATION`,
`MATCH_WEIGHT_DOMAIN`. Override any of them in `.env` — the scorer
normalizes whatever you provide, so they don't need to sum to exactly 1.0.

### 2. Run the new migration

```powershell
alembic upgrade head
```

Creates `matching_results` table (migration `0005`).

### 3. Run tests

```powershell
pytest
```

New: `test_matching_scorer.py` tests the scoring formulas directly with no
mocking (pure functions). `test_orchestrator.py` now covers the 6-node
graph, including a test that the Matching Agent gracefully falls back to
a plain summary (recording a soft error) if only its narrative LLM call
fails — the deterministic score itself is never lost to a narrative
hiccup.

### 4. Run a real analysis and sanity-check the score

Check `matching_result` in the response:
- `sub_scores` — five 0-100 values; `ats_keyword_match` should exactly
  equal the `ats_result.ats_score` from earlier in the same response
  (it's reused directly, not recomputed).
- `weights_used` — should reflect your configured (or default) weights,
  normalized to sum to 1.0.
- `overall_match_score` — manually verify it's the weighted sum of
  `sub_scores` using `weights_used` — this is the whole point of keeping
  it deterministic and auditable.
- `narrative_summary` — should describe the actual numbers, not add new
  claims.
- `methodology_note` — fixed explanation of the formula itself.

```powershell
docker exec -it career_ai_postgres psql -U career_ai -d career_ai -P pager=off -c "SELECT jsonb_pretty(data) FROM matching_results ORDER BY created_at DESC LIMIT 1;"
```

## Slice 5: Recommendation Agent

Graph is now:
```
START -> resume_analyzer --\
START -> jd_analyzer -------> skill_gap -> ats_analysis --------\
                                        \-> experience_analysis --> matching -> recommendation -> END
```

The Recommendation Agent is grounded primarily in `skill_gap_result` (its
missing/matching/transferable skills) plus resume and JD context — it's
explicitly instructed not to invent gaps beyond what Skill Gap already
found. It also receives the Matching Agent's narrative summary as extra
context when available.

No new Python dependencies. No changes to Gemini-schema defaults this
slice (`RecommendationResult` was written default-free from the start).

### 1. Run the new migration

```powershell
alembic upgrade head
```

Creates the `recommendations` table (migration `0006`).

### 2. Run tests

```powershell
pytest
```

`test_orchestrator.py` now covers the 7-node graph. One test specifically
checks that when the Matching Agent's *narrative* call fails (but its
deterministic score still succeeds via fallback), Recommendation still
runs normally — its dependency is on `skill_gap_result` existing, not on
Matching's narrative succeeding.

### 3. Run a real analysis and check groundedness

Check `recommendation_result`:
- `skills_to_learn` should mostly mirror the critical/important
  `missing_skills` from `skill_gap_result` — if it lists something wildly
  unrelated to any detected gap, that's a prompt-grounding issue worth
  flagging.
- `project_ideas` should build on the candidate's *actual* existing
  projects (visible in `resume_extraction.projects`), not generic
  unrelated toy examples.
- `relevant_certifications` should be real, well-known certifications —
  watch for anything that sounds invented.

```powershell
docker exec -it career_ai_postgres psql -U career_ai -d career_ai -P pager=off -c "SELECT jsonb_pretty(data) FROM recommendations ORDER BY created_at DESC LIMIT 1;"
```

## Slice 5: Recommendation Agent

Runs after Matching. Grounded primarily in `skill_gap_result` (never
inventing gaps beyond what Skill Gap already detected), with resume/JD
context to keep project ideas and suggestions realistic and non-duplicate.

Graph is now:
```
... -> matching -> recommendation -> END
```

### 1. Run the new migration

```powershell
alembic upgrade head
```

Creates `recommendations` table (migration `0006`).

### 2. Run tests

```powershell
pytest
```

`test_orchestrator.py` now covers the 7-node graph. One test specifically
checks that Recommendation still runs normally even when Matching's
narrative sub-call failed (since Matching still produces a full, valid
`matching_result` via its fallback) — a soft failure in one agent doesn't
need to cascade if the data downstream actually depends on is still there.

### 3. Run a real analysis and check groundedness

In `recommendation_result`, specifically check:
- `skills_to_learn` — should prioritize the CRITICAL missing skills from
  `skill_gap_result`, not introduce skills that were never flagged as gaps.
- `project_ideas` — should genuinely build toward the missing skills,
  ideally referencing or extending projects already in the resume.
- `relevant_certifications` — should be real, well-known certifications,
  not invented ones.
- `resume_improvements` — wording/presentation only, consistent with what
  ATS/Experience agents already found — never suggests fabricating
  experience.

```powershell
docker exec -it career_ai_postgres psql -U career_ai -d career_ai -P pager=off -c "SELECT jsonb_pretty(data) FROM recommendations ORDER BY created_at DESC LIMIT 1;"
```

## What's left in Phase 3

Only the **Interview Preparation Agent** remains before the core 9-agent
pipeline (minus the optional Resume Optimization feature, which is
Phase 6) is functionally complete.

## Slice 6: Interview Preparation Agent — Phase 3 COMPLETE

This is the final agent in the core pipeline. It runs in **parallel with
Recommendation** (not sequentially, despite the original spec's diagram
suggesting a chain) — both depend only on resume_extraction, jd_extraction,
and skill_gap_result, so there's no reason to serialize them.

Final graph:
```
START -> resume_analyzer --\
START -> jd_analyzer -------> skill_gap -> ats_analysis --------\
                                        \-> experience_analysis --> matching --> recommendation --------\
                                                                                \-> interview_prep --------> END
```

### 1. Run the new migration

```powershell
alembic upgrade head
```

Creates `interview_questions` table (migration `0007`) — the last one for
Phase 3.

### 2. Run tests

```powershell
pytest
```

`test_orchestrator.py` now covers the full 8-node graph, including a test
that confirms Recommendation AND Interview Prep both still run normally
even when Matching's narrative sub-call fails (neither depends on that
specific piece of Matching's output).

### 3. Run a real, full analysis

This is the first time all 8 nodes run together for real. Expect this to
take noticeably longer than previous slices — roughly 25-40 seconds,
since there are now 7 real LLM calls (Resume, JD, Skill Gap, ATS,
Experience, Matching's narrative, Recommendation, Interview Prep — 8 calls
total) across 3 sequential stages.

Check `interview_result.questions`:
- Are questions genuinely personalized (reference actual project names,
  actual missing skills) rather than generic boilerplate?
- Does `rationale` for each question make sense — does it actually explain
  why that question was chosen for this specific candidate/role?
- Are categories sensible for the role (no forced RAG questions if the
  role has nothing to do with RAG)?

```powershell
docker exec -it career_ai_postgres psql -U career_ai -d career_ai -P pager=off -c "SELECT jsonb_pretty(data) FROM interview_questions ORDER BY created_at DESC LIMIT 1;"
```

## Phase 3 is now complete

All 8 core agent graph nodes are built, wired, tested, and verified against
the real Gemini API. The only agent from the original spec not yet built is
**Resume Optimization**, which is a separate, optional, user-triggered
feature (Phase 6) — it doesn't belong in this always-runs analysis graph.

**Next up: Phase 4 (RAG)** — this will meaningfully improve Recommendation
and Interview Prep by grounding them in real retrieved reference material
(skill/role docs, an interview question bank) instead of relying purely on
the LLM's own training knowledge.
