# Prompt Engineering

Prompt engineering is the practice of designing inputs to an LLM to
reliably produce the desired output - covering everything from instruction
phrasing to output format constraints to few-shot examples.

## Core techniques

- **Clear, specific instructions**: vague prompts produce vague or
  inconsistent outputs. Explicitly stating constraints (length, format,
  what to avoid) measurably improves reliability.
- **Structured output / schema-constrained generation**: rather than
  asking a model to "return JSON" in free text and hoping it complies,
  modern APIs (including Gemini's `response_schema` parameter) let you
  pass a formal schema that constrains the model's output shape directly
  - far more reliable than prompt instructions alone.
- **Few-shot examples**: showing the model 1-3 examples of the desired
  input/output pattern before the real request, useful when the task is
  ambiguous from instructions alone.
- **Chain-of-thought / step-by-step reasoning**: asking the model to work
  through intermediate steps before the final answer, often improving
  accuracy on tasks requiring multi-step reasoning.
- **Negative constraints**: explicitly telling the model what NOT to do
  (e.g. "do not invent skills not present in the resume") is often as
  important as positive instructions, especially for tasks where
  hallucination/fabrication is a risk.

## Hallucination mitigation in prompts

For tasks where fabrication is a real risk (e.g. extracting structured
data, generating recommendations based on detected gaps), explicit
instructions like "if a field is not present, leave it empty rather than
guessing" measurably reduce fabricated output, though they don't
eliminate it entirely - defense in depth (validation after generation,
not just prompting) is still necessary for production reliability.

## Versioning prompts

Treating prompts as versioned artifacts (not just inline strings buried in
code) makes it possible to track how prompt changes affect output quality
over time, and makes prompt changes reviewable the same way code changes
are.

## Common interview-relevant depth signals

A candidate with genuine prompt engineering experience should be able to
give a concrete example of a prompt that didn't work, why it didn't work,
and what specific change fixed it - vague claims of "I'm good at prompt
engineering" without a concrete example are a weak signal.
