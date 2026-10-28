"""Start the isolated local stack. Stops only processes owned by this launcher."""

import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
children = []


def listening(port):
    with socket.socket() as s:
        s.settimeout(0.2)
        return s.connect_ex(("127.0.0.1", port)) == 0


def launch(argv, port=None):
    if port and listening(port):
        raise RuntimeError(f"Port {port} is in use. Stop the existing local process before starting a second stack.")
    p = subprocess.Popen(argv, cwd=ROOT, start_new_session=True)
    children.append(p)
    return p


def stop(*_):
    for p in reversed(children):
        if p.poll() is None:
            os.killpg(p.pid, signal.SIGTERM)
    raise SystemExit(0)


signal.signal(signal.SIGINT, stop)
signal.signal(signal.SIGTERM, stop)
try:
    subprocess.run(["docker", "compose", "up", "-d", "--wait", "postgres"], check=True)
    subprocess.run(["uv", "run", "alembic", "upgrade", "head"], check=True)
    launch(["uv", "run", "moto_server", "-H", "127.0.0.1", "-p", "59000"], 59000)
    for _ in range(30):
        if listening(59000):
            break
        time.sleep(0.2)
    launch(
        ["uv", "run", "uvicorn", "scos.app:app", "--app-dir", "services/api", "--host", "127.0.0.1", "--port", "8100"],
        8100,
    )
    for _ in range(50):
        if listening(8100):
            break
        time.sleep(0.2)
    env = dict(os.environ, PYTHONPATH="services/api")
    p = subprocess.Popen(["uv", "run", "python", "-m", "scos.worker"], cwd=ROOT, env=env, start_new_session=True)
    children.append(p)
    launch(["npm", "--prefix", "apps/web", "run", "dev"], 3100)
    (ROOT / ".runtime").mkdir(exist_ok=True)
    (ROOT / ".runtime/pids.json").write_text(json.dumps([p.pid for p in children]))
    print(
        "\nScreen Central OS: http://127.0.0.1:3100\nLocal fixture sign-in; live writes disabled. Ctrl+C stops app processes.\n",
        flush=True,
    )
    while all(p.poll() is None for p in children):
        time.sleep(1)
    raise RuntimeError("A local process exited. See the preceding error output.")
finally:
    for p in reversed(children):
        if p.poll() is None:
            os.killpg(p.pid, signal.SIGTERM)
