# GenAI Engineering Interview Questions (Reference Bank)

These are reference question patterns for probing GenAI engineering depth.
They are meant as inspiration for generating personalized questions, not
to be used verbatim without connecting them to a specific candidate's
actual experience.

## Architecture and design judgment

- Walk me through how you decided which parts of your pipeline needed an
  LLM call versus deterministic code. (Good candidates recognize that not
  every step benefits from an LLM - e.g. a score calculation is often
  better as a deterministic formula than an LLM guess.)
- How do you handle a step in your pipeline failing - does the whole
  request fail, or does it degrade gracefully?
- What was your approach to reducing hallucination in [a specific feature
  of their project]?

## Structured output and reliability

- How did you ensure the LLM's output matched the schema your application
  expected? What did you do when it didn't?
- What happens in your system if the LLM returns malformed or incomplete
  output?

## RAG-specific (only relevant if the candidate's project/role involves RAG)

- How did you choose your chunking strategy, and what trade-offs did you
  consider?
- How do you evaluate whether your retrieval is actually returning
  relevant results?
- What would you do if retrieval started returning irrelevant chunks as
  your knowledge base grew?

## Agent orchestration (only relevant if the candidate's project involves
multi-agent systems)

- Which parts of your agent pipeline genuinely run in parallel, and how do
  you know?
- How do you prevent one agent's failure from silently corrupting the
  final output?

## Cost and latency awareness

- How many LLM calls does a single end-to-end request in your system make,
  and did that influence any of your design decisions?
- What would you change about your architecture if your free-tier API
  quota suddenly became much more restrictive?
