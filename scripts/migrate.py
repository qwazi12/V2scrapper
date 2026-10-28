"""Serialize additive Alembic upgrades against the configured isolated SCOS database."""

import os
import subprocess
import sys
from scos.config import ROOT, validate
from scos.db import connect

validate()
with connect() as c:
    c.execute("SELECT pg_advisory_lock(hashtextextended(%s,0))", ("scos:migrations",))
    try:
        subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], cwd=ROOT, env=os.environ, check=True)
    finally:
        c.execute("SELECT pg_advisory_unlock(hashtextextended(%s,0))", ("scos:migrations",))
