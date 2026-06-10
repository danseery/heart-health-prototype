# Local Development

This prototype runs locally only. Do not use real patient data, do not create Azure resources, and do not push changes unless explicitly approved.

## Backend

```bash
python -m venv backend/.venv
```

## Frontend

Windows:

```powershell
.\backend\.venv\Scripts\python.exe -m pip install --upgrade pip
.\backend\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
Copy-Item .env.example backend\.env
npm install --prefix frontend
```

Linux / WSL:

```bash
backend/.venv/bin/python -m pip install --upgrade pip
backend/.venv/bin/python -m pip install -r backend/requirements.txt
cp .env.example backend/.env
npm install --prefix frontend
```

## Start the App

Start the full app from the repo root:

```bash
python scripts/dev.py
```

Or on Linux / WSL:

```bash
./scripts/dev.sh
```

This starts:

- FastAPI on `http://127.0.0.1:8000`
- Vite on `http://127.0.0.1:5173`

Health check:

```bash
curl http://127.0.0.1:8000/api/health
```

If you prefer the VS Code UI, run the `HeartHealth: Start Local App` task from the command palette.

## Local Data Rules

- Use seeded dummy data only.
- Keep SQLite databases under `backend/local_data/` or another ignored local path.
- Keep environment overrides in ignored `.env` files.
- Do not export, screenshot, or commit real health information.

## Change Hygiene

- Every behavior change should include a focused test when practical.
- If a test is not practical for a small UI or workflow change, update an MD file to capture the decision, tradeoff, or user-facing behavior.
- Keep commits on named feature branches until the slice is tested and approved for merge into `main`.
- Do not push or create Azure infrastructure unless explicitly approved.
