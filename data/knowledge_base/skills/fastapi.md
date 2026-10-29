# FastAPI

FastAPI is a modern Python web framework for building APIs, built on top
of Starlette (ASGI) and Pydantic. It's widely used for both traditional
REST APIs and, increasingly, as the backend layer for LLM/AI applications
that need to expose model inference as an HTTP service.

## Why it's popular for AI/ML backends specifically

- **Pydantic integration**: request/response validation is declared via
  type hints and Pydantic models, which maps naturally onto the
  structured-output patterns common in LLM applications.
- **Automatic interactive docs**: FastAPI generates OpenAPI/Swagger
  documentation automatically from the code, useful for quickly testing
  endpoints during development.
- **Async support**: built on ASGI, so it natively supports async
  request handlers - useful when an endpoint needs to wait on a slow
  external call (like an LLM API) without blocking the whole server.
- **Dependency injection**: FastAPI's `Depends()` system makes it easy to
  share things like database sessions or authentication logic across
  routes cleanly.

## Common architecture patterns

- **Background tasks**: for long-running operations (like a multi-agent
  pipeline that takes 30+ seconds), returning an immediate response and
  processing the work in the background (or via a task queue) is a
  common pattern, with the client polling a status endpoint for the
  result.
- **Dependency-injected database sessions**: a common pattern is a
  `get_db()` generator function that yields a session and guarantees
  cleanup via try/finally, injected into routes via `Depends()`.
- **Separating routes from business logic**: routes should stay thin,
  delegating actual logic to a services/ layer - this keeps routes
  testable and keeps business logic reusable outside the HTTP context.

## Common interview-relevant depth signals

A candidate with genuine FastAPI experience should be able to explain why
they chose sync vs. async for their specific endpoints (not just "FastAPI
is async"), how they structured error handling (custom exceptions mapped
to HTTP status codes vs. generic 500s), and how they validated/sanitized
user input before it reached business logic.
