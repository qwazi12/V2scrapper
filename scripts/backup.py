"""Local backup and restore drill; never restores over an existing database."""

import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
import psycopg
from psycopg import sql
from scos.db import connect, all_rows, sha, clean
from scos.config import ROOT, RUNTIME, DATABASE_URL

stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
folder = RUNTIME / "backups" / stamp
folder.mkdir(parents=True)
cmd = ["docker", "compose", "exec", "-T", "postgres"]
dump = subprocess.run(
    cmd + ["pg_dump", "-U", "scos", "-d", "scos_local", "--no-owner"], cwd=ROOT, capture_output=True, check=True
).stdout
(folder / "database.sql").write_bytes(dump)
shutil.copytree(RUNTIME / "objects", folder / "objects", dirs_exist_ok=True)
with connect() as c:
    exports = clean(all_rows(c, "SELECT id,sha256,object_key FROM exports ORDER BY id"))
    attempts = clean(all_rows(c, "SELECT id,state,external_post_id FROM publication_attempts ORDER BY id"))
manifest = {
    "database_sha256": sha(dump),
    "exports": exports,
    "publication_attempts": attempts,
    "namespace": "scos-local",
    "live_writes": False,
}
for ex in exports:
    assert sha((folder / ex["object_key"]).read_bytes()) == ex["sha256"]
if "--restore-drill" in sys.argv:
    name = "scos_restore_" + stamp
    with psycopg.connect(DATABASE_URL.rsplit("/", 1)[0] + "/postgres", autocommit=True) as c:
        c.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
    subprocess.run(
        cmd + ["psql", "-X", "-v", "ON_ERROR_STOP=1", "-U", "scos", "-d", name],
        input=dump,
        cwd=ROOT,
        capture_output=True,
        check=True,
    )
    from psycopg.rows import dict_row

    with psycopg.connect(DATABASE_URL.rsplit("/", 1)[0] + "/" + name, row_factory=dict_row) as c:
        assert clean(c.execute("SELECT id,sha256,object_key FROM exports ORDER BY id").fetchall()) == exports
        assert (
            clean(c.execute("SELECT id,state,external_post_id FROM publication_attempts ORDER BY id").fetchall())
            == attempts
        )
    manifest["restore_drill"] = {
        "database": name,
        "status": "passed",
        "exports": len(exports),
        "attempts": len(attempts),
        "note": "Isolated recovery database retained; no worker or publisher attached.",
    }
(folder / "manifest.json").write_text(json.dumps(manifest, indent=2))
print(json.dumps({"backup": str(folder), "restore_drill": manifest.get("restore_drill")}, indent=2))
