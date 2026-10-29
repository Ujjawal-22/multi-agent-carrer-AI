# GenAI Engineer — Typical Role Expectations

This describes general industry expectations for a GenAI Engineer role at
the entry-to-mid level. This is GENERAL REFERENCE CONTEXT about what the
role archetype typically involves - it is not a substitute for the actual
requirements of any specific job description, and should never be used to
claim a candidate is missing something that the specific job they're
applying to didn't actually require.

## Typical core skills

- Strong Python fundamentals, including type hints and testing.
- Experience calling LLM APIs (OpenAI, Anthropic, Gemini, or similar) and
  handling their failure modes (rate limits, malformed output, timeouts).
- Structured output / schema-constrained generation, to get reliable
  machine-readable data out of an LLM rather than parsing free text.
- Prompt engineering, including iterating on prompts based on observed
  failures, not just initial design.

## Commonly expected, but varies by specific job

- RAG pipeline experience: chunking, embeddings, vector databases,
  retrieval, and ideally some understanding of hybrid retrieval.
- Agent orchestration frameworks (LangGraph, LangChain, CrewAI, or
  similar) for multi-step or multi-agent workflows.
- Backend API development (commonly FastAPI in the Python ecosystem) to
  expose GenAI functionality as a service.
- Observability/tracing for LLM calls (e.g. Langfuse, LangSmith) - this
  is a growing expectation as GenAI systems move toward production.

## Less commonly required at entry/mid level, but a strong differentiator

- LLM evaluation methodology (not just "it seems to work," but actual
  measured metrics on a test set).
- Fine-tuning or model customization experience.
- Experience with multiple LLM providers and provider-abstraction design
  (i.e. not hard-coding a single vendor's SDK throughout the codebase).

## What typically distinguishes strong candidates in interviews

Being able to explain WHY specific architectural choices were made (why
this framework, why this chunking size, why this retry strategy) rather
than just listing technologies used. Vague familiarity with buzzwords
without the ability to explain trade-offs is a common weak signal
interviewers specifically probe for.
