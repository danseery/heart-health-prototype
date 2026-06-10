from __future__ import annotations

import atexit
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = REPO_ROOT / "backend"
FRONTEND_DIR = REPO_ROOT / "frontend"
VITE_ENTRYPOINT = FRONTEND_DIR / "node_modules" / "vite" / "bin" / "vite.js"


def find_backend_python() -> Path | None:
    candidates = [
        BACKEND_DIR / ".venv" / "Scripts" / "python.exe",
        BACKEND_DIR / ".venv" / "bin" / "python",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def find_node() -> Path | None:
    candidates = []
    candidates.extend(
        [
            Path("C:/Program Files/nodejs/node.exe"),
            Path.home()
            / ".cache"
            / "codex-runtimes"
            / "codex-primary-runtime"
            / "dependencies"
            / "node"
            / "bin"
            / "node.exe",
        ]
    )
    path_node = shutil.which("node")
    if path_node:
        candidates.append(Path(path_node))
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def stream_output(name: str, process: subprocess.Popen[str]) -> None:
    assert process.stdout is not None
    for line in process.stdout:
        print(f"[{name}] {line}", end="")


def terminate_processes(processes: list[subprocess.Popen[str]]) -> None:
    for process in processes:
        if process.poll() is None:
            process.terminate()
    deadline = time.time() + 5
    while time.time() < deadline:
        if all(process.poll() is not None for process in processes):
            return
        time.sleep(0.1)
    for process in processes:
        if process.poll() is None:
            process.kill()


def main() -> int:
    backend_python = find_backend_python()
    if backend_python is None:
        print("Missing backend virtual environment at backend/.venv.", file=sys.stderr)
        print("Create it first with: python -m venv backend/.venv", file=sys.stderr)
        return 1

    if not VITE_ENTRYPOINT.exists():
        print("Missing frontend dependencies in frontend/node_modules.", file=sys.stderr)
        print("Install them first with: npm install --prefix frontend", file=sys.stderr)
        return 1

    node = find_node()
    if node is None:
        print("Unable to find a Node.js runtime.", file=sys.stderr)
        print("Install Node.js or run this inside a Codex runtime-enabled environment.", file=sys.stderr)
        return 1

    processes: list[subprocess.Popen[str]] = []
    atexit.register(lambda: terminate_processes(processes))

    backend = subprocess.Popen(
        [
            str(backend_python),
            "-m",
            "uvicorn",
            "app.main:app",
            "--reload",
            "--host",
            "127.0.0.1",
            "--port",
            "8000",
        ],
        cwd=BACKEND_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        shell=False,
        text=True,
    )
    frontend_command = (
        f'"{node}" "{VITE_ENTRYPOINT}" --host 127.0.0.1 --port 5173'
    )
    frontend = subprocess.Popen(
        frontend_command,
        cwd=FRONTEND_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        shell=True,
        text=True,
    )
    processes.extend([backend, frontend])

    print("HeartHealth local app starting...")
    print("Backend:  http://127.0.0.1:8000")
    print("Frontend: http://127.0.0.1:5173")

    threads = [
        threading.Thread(target=stream_output, args=("backend", backend), daemon=True),
        threading.Thread(target=stream_output, args=("frontend", frontend), daemon=True),
    ]
    for thread in threads:
        thread.start()

    try:
        while True:
            if backend.poll() is not None:
                terminate_processes(processes)
                return backend.returncode or 1
            if frontend.poll() is not None:
                terminate_processes(processes)
                return frontend.returncode or 1
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nStopping HeartHealth local app...")
        terminate_processes(processes)
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
