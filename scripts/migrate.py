"""Serialize additive Alembic upgrades against the configured isolated SCOS database."""

import os
import subprocess
import sys
from scos.config import ROOT, validate, DATABASE_SCHEMA, DATABASE_URL, database_connect_args
from scos.db import connect
from psycopg import sql
import psycopg

validate()
if os.getenv("SCOS_MIGRATIONS_ON_START", "true") == "false":
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    head = ScriptDirectory.from_config(Config(str(ROOT / "alembic.ini"))).get_current_head()
    with connect() as c:
        revision = c.execute("SELECT version_num FROM alembic_version").fetchone()["version_num"]
        if revision != head:
            raise RuntimeError("SCOS_MIGRATION_REQUIRED: apply the release migration with the isolated migration role")
    sys.exit(0)
if DATABASE_SCHEMA != "public":
    with psycopg.connect(DATABASE_URL, **database_connect_args()) as bootstrap:
        bootstrap.execute(sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(sql.Identifier(DATABASE_SCHEMA)))
with connect() as c:
    c.execute("SELECT pg_advisory_lock(hashtextextended(%s,0))", ("scos:migrations",))
    try:
        subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], cwd=ROOT, env=os.environ, check=True)
    finally:
        c.execute("SELECT pg_advisory_unlock(hashtextextended(%s,0))", ("scos:migrations",))
