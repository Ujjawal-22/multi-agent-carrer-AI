# Python Interview Questions (Reference Bank)

## Language fundamentals

- Explain the difference between a list and a generator, and when you'd
  choose one over the other.
- What's the difference between `@staticmethod`, `@classmethod`, and a
  regular instance method?
- How does Python's garbage collection handle reference cycles?

## Type hints and modern Python

- How do you use type hints to catch bugs before runtime, and what tool
  do you use to actually enforce them (mypy, pyright, etc.)?
- Explain the difference between `list[str]` and `List[str]` - when did
  this change, and why does it matter for a project's minimum Python
  version?

## Pydantic (highly relevant for GenAI/API roles)

- Walk me through how you'd design a Pydantic model as a schema for an
  LLM's structured output. What constraints do you need to keep in mind?
- What's the difference between a Pydantic field default and a required
  field, and have you run into a case where a default caused an actual
  problem?

## Async Python

- When does async actually help in Python, versus when is it just added
  complexity with no real benefit?
- What's the difference between `asyncio.gather` and running tasks
  sequentially with `await`?

## Testing

- How do you test code that calls an external API (like an LLM) without
  making real API calls in your test suite?
- What's the difference between a unit test and an integration test in
  your own project, and give a concrete example of each.
