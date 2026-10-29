# Phase 2 Setup — Document Processing

## 1. Install Tesseract OCR (Windows)

`pytesseract` is only a wrapper — it needs the actual Tesseract engine
installed separately.

1. Download from the UB-Mannheim Tesseract build:
   https://github.com/UB-Mannheim/tesseract/wiki
2. Install (default path: `C:\Program Files\Tesseract-OCR\tesseract.exe`,
   already matching the default `TESSERACT_CMD` in config).
3. Verify:
   ```powershell
   & "C:\Program Files\Tesseract-OCR\tesseract.exe" --version
   ```

## 2. Install dependencies and migrate

```powershell
pip install -r requirements.txt
alembic upgrade head
```

## 3. Try it via Swagger UI (`http://localhost:8000/docs`)

- **POST /api/resumes/upload** — upload a PDF/DOCX resume
- **POST /api/jobs** — paste JD text as `{"title": "...", "text": "..."}`
- **POST /api/jobs/upload** — upload a JD file

## Troubleshooting

**`TesseractNotFoundError`:** Tesseract isn't installed, or
`TESSERACT_CMD` in `.env` doesn't match your install path.

**422 "No readable text could be extracted":** expected, honest failure
behavior for an unreadable/corrupted file — not a bug.
