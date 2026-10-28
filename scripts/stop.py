"""Stop only launcher process groups whose current working directory is this repository."""

import json
import os
from pathlib import Path
import signal
import subprocess

root = Path(__file__).resolve().parents[1]
path = root / ".runtime/pids.json"
if path.exists():
    for pid in json.loads(path.read_text()):
        try:
            proc_cwd = Path(f"/proc/{pid}/cwd")
            if proc_cwd.exists():
                owned = proc_cwd.resolve() == root
            else:
                result = subprocess.run(
                    ["lsof", "-a", "-p", str(pid), "-d", "cwd", "-Fn"], capture_output=True, text=True
                )
                owned = ("n" + str(root)) in result.stdout.splitlines()
            if owned and os.getpgid(pid) == pid:
                os.killpg(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
    path.unlink()
print("Stopped owned launcher processes. PostgreSQL data is retained.")
