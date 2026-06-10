# Backend

FastAPI backend for HeartHealth AI local development.

## Local Setup

```powershell
cd C:\Users\danie\OneDrive\Documents\Hearty\backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item ..\.env.example .env
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Health check:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/health
```

## Security Notes

- The local database path is ignored by git.
- `.env` is ignored by git.
- The API starts with strict local CORS origins.
- Sensitive health payloads should not be logged.
