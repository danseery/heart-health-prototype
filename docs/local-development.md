# Local Development

This prototype runs locally only. Do not use real patient data, do not create Azure resources, and do not push changes unless explicitly approved.

## Backend

```powershell
cd C:\Users\danie\OneDrive\Documents\Hearty\backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item ..\.env.example .env
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/api/health`.

## Frontend

```powershell
cd C:\Users\danie\OneDrive\Documents\Hearty\frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173`.

## Local Data Rules

- Use seeded dummy data only.
- Keep SQLite databases under `backend/local_data/` or another ignored local path.
- Keep environment overrides in ignored `.env` files.
- Do not export, screenshot, or commit real health information.
