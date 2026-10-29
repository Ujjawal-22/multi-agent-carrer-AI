# Backend Engineer — Typical Role Expectations

GENERAL REFERENCE CONTEXT about the role archetype - not a substitute for
any specific job description's actual stated requirements.

## Typical core skills

- API design (REST, sometimes GraphQL) and the ability to explain
  trade-offs in endpoint design, versioning, and error handling.
- A relational database (PostgreSQL, MySQL) including schema design,
  indexing, and migrations.
- An ORM or query layer (SQLAlchemy, Django ORM, Prisma, etc.) and
  understanding when to drop to raw SQL instead.
- Authentication/authorization fundamentals.
- Testing (unit and integration) and CI/CD familiarity.

## Commonly expected, but varies by specific job

- Containerization (Docker) and basic orchestration understanding.
- Caching strategies (Redis or similar) for performance-sensitive
  endpoints.
- Message queues or background task processing for long-running
  operations.
- Cloud platform experience (AWS, GCP, or Azure) at least at a basic
  deployment level.

## What typically distinguishes strong candidates in interviews

Being able to discuss a real production incident or performance problem
they diagnosed and fixed, not just features they built. Understanding the
difference between "it works on my machine" and what's actually needed
for a reliable, observable production service (logging, error handling,
graceful degradation under failure).
