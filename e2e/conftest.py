import os
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
API_PORT = 8100   # puertos propios para no chocar con los de desarrollo
WEB_PORT = 5200


def _port_free(port: int) -> bool:
    with socket.socket() as s:
        return s.connect_ex(("127.0.0.1", port)) != 0


def _wait_for(url: str, timeout: float = 20) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(url, timeout=1)
            return
        except Exception:
            time.sleep(0.2)
    raise RuntimeError(f"El servidor no respondió en {url}")


@pytest.fixture(scope="session")
def app_url():
    """Levanta backend (FastAPI) y frontend (Vite) reales y los cierra al terminar."""
    for port in (API_PORT, WEB_PORT):
        assert _port_free(port), f"El puerto {port} está ocupado"

    api = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--port", str(API_PORT)],
        cwd=ROOT / "backend-fastapi", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    web = subprocess.Popen(
        ["node", "node_modules/vite/bin/vite.js", "--port", str(WEB_PORT), "--strictPort"],
        cwd=ROOT / "frontend", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        env={**os.environ, "API_URL": f"http://localhost:{API_PORT}"},
    )
    try:
        _wait_for(f"http://127.0.0.1:{API_PORT}/items")
        _wait_for(f"http://localhost:{WEB_PORT}")
        yield f"http://localhost:{WEB_PORT}"
    finally:
        for p in (web, api):
            p.terminate()
            p.wait(timeout=10)
