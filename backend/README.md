# Backend

FastAPI backend for HeartHealth AI local development.

## Local Setup

```bash
python -m venv backend/.venv
```

Start the full app from the repo root:

```bash
python scripts/dev.py
```

Health check:

```bash
curl http://127.0.0.1:8000/api/health
```

## Security Notes

- The local database path is ignored by git.
- `.env` is ignored by git.
- The API starts with strict local CORS origins.
- Sensitive health payloads should not be logged.
