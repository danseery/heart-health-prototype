$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $repoRoot "backend\.venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
  throw "Missing backend virtual environment at backend/.venv. Create it first with: py -3.12 -m venv backend\.venv"
}

& $python (Join-Path $PSScriptRoot "dev.py")
