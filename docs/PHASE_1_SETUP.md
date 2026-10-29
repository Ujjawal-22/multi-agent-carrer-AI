# Phase 1 Setup — Windows / PowerShell

Assumes: Docker Desktop installed and running, Python 3.12 installed
alongside your system Python (needed because some compiled dependencies
don't yet have prebuilt wheels for very new Python versions), PowerShell
in VS Code's integrated terminal.

## 1. Place the project and create .env

Extract the project to a folder, e.g. `C:\resume.system\multi-agent-career-ai`,
open it in VS Code, then:

```powershell
Copy-Item .env.example .env
```

Open `.env` and paste your real `GEMINI_API_KEY`.

## 2. Start Postgres and Qdrant via Docker

From the project root:

```powershell
docker compose up -d postgres qdrant
docker ps
```

Confirm `career_ai_postgres` and `career_ai_qdrant` are both `Up`.

## 3. Create the Python virtual environment

From `backend/`, using your Python 3.12 interpreter specifically (adjust
the path to match your actual install location):

```powershell
cd backend
C:\Users\<you>\AppData\Local\Programs\Python\Python312\python.exe -m venv venv
venv\Scripts\activate
```

## 4. Install dependencies and run

```powershell
pip install --upgrade pip
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## 5. Verify

- `http://localhost:8000/` — JSON welcome message
- `http://localhost:8000/docs` — Swagger UI
- `http://localhost:8000/api/health` — `"status": "ok"`,
  `"database": "ok"`

## 6. Run tests

```powershell
pytest
```

## Troubleshooting

**`psycopg2` fails to build:** confirm you're using the Python 3.12 venv,
not a newer version — compiled dependencies may lack prebuilt Windows
wheels for very recent Python releases.

**`docker compose` not found:** older Docker Desktop uses the hyphenated
`docker-compose` instead.

**Health check shows a database error:** confirm the postgres container
is actually healthy (`docker ps`) and nothing else is using port 5432.
