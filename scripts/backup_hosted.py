"""Encrypted private-schema + Storage backup and an isolated offline PostgreSQL restore drill.

Reads only the configured SCOS staging project. Does not restore into any existing database or bucket.
Run with the migration operator credential and a separate SCOS_BACKUP_ENCRYPTION_KEY.
"""

import argparse
import json
import os
import re
import subprocess
import tempfile
import time
from pathlib import Path
from urllib.parse import urlsplit, unquote
from uuid import uuid4
from psycopg import sql
from scos import config, storage
from scos.db import connect, sha, clean, now
from scos.backup_crypto import key_from_env, encrypt, decrypt

IMAGE = "postgres:17-alpine@sha256:266d3c257594e195b309ae9d1805e54c788f1d7b375f56bf6c367aac6c917e7b"


def docker(args, *, env=None, data=None, timeout=240):
    result = subprocess.run(["docker", *args], input=data, env=env, capture_output=True, timeout=timeout)
    if result.returncode:
        # Do not emit connection strings, data rows or credentials in failure logs.
        raise RuntimeError("Isolated backup/restore operation failed at Docker step " + args[0])
    return result.stdout


def table_manifest(c, schema):
    tables = c.execute("SELECT tablename FROM pg_tables WHERE schemaname=%s ORDER BY tablename", (schema,)).fetchall()
    result = {}
    for table in tables:
        name = table["tablename"]
        if name == "hosted_owner_policy":
            continue  # The backup must not carry the owner allowlist into a recovery environment.
        rows = c.execute(
            sql.SQL("SELECT row_to_json(t) AS row FROM {} t").format(sql.Identifier(schema, name))
        ).fetchall()
        values = sorted(json.dumps(row["row"], sort_keys=True, separators=(",", ":")) for row in rows)
        result[name] = {"rows": len(values), "sha256": sha(values)}
    return result


def object_inventory():
    client = storage.client()
    keys, offset = [], 0
    while True:
        response = client.request(
            "POST",
            "object/list/" + config.BUCKET,
            json={"prefix": "objects", "limit": 1000, "offset": offset, "sortBy": {"column": "name", "order": "asc"}},
        )
        if response.status_code != 200 or not isinstance(response.json(), list):
            raise RuntimeError("Private Storage inventory is unavailable")
        rows = response.json()
        for row in rows:
            key = "objects/" + row.get("name", "")
            storage.safe_key(key)
            if key in keys:
                raise RuntimeError("Storage inventory pagination repeated an object")
            keys.append(key)
        if len(rows) < 1000:
            return keys
        offset += len(rows)


def referenced_objects(c):
    refs = set()

    def visit(value):
        if isinstance(value, str) and value.startswith("objects/"):
            storage.safe_key(value)
            refs.add(value)
        elif isinstance(value, dict):
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    for table in ("media_assets", "asset_rights", "source_records", "exports"):
        for row in c.execute(
            sql.SQL("SELECT row_to_json(t) AS row FROM {} t").format(sql.Identifier(table))
        ).fetchall():
            visit(row["row"])
    return refs


def dump_database(snapshot):
    url = urlsplit(config.DATABASE_URL)
    env = {
        **os.environ,
        "PGHOST": url.hostname,
        "PGPORT": str(url.port or 5432),
        "PGUSER": unquote(url.username or ""),
        "PGPASSWORD": unquote(url.password or ""),
        "PGDATABASE": "postgres",
        "PGSSLMODE": "verify-full",
        "PGSSLROOTCERT": "/certs/supabase.crt",
    }
    cert = config.ROOT / "certs/supabase-prod-ca-2021.crt"
    args = ["run", "--rm", "--mount", f"type=bind,source={cert},target=/certs/supabase.crt,readonly"]
    for name in ("PGHOST", "PGPORT", "PGUSER", "PGPASSWORD", "PGDATABASE", "PGSSLMODE", "PGSSLROOTCERT"):
        args += ["--env", name]
    return docker(
        args
        + [
            IMAGE,
            "pg_dump",
            "--format=custom",
            "--no-owner",
            "--no-acl",
            "--lock-wait-timeout=5000",
            "--schema=" + config.DATABASE_SCHEMA,
            "--snapshot=" + snapshot,
            "--exclude-table-data=" + config.DATABASE_SCHEMA + ".hosted_owner_policy",
        ],
        env=env,
    )


def restore_drill(folder, key, label):
    manifest = json.loads(decrypt((folder / "manifest.enc").read_bytes(), key, label + ":manifest"))
    dump = decrypt((folder / "database.enc").read_bytes(), key, label + ":database")
    if sha(dump) != manifest["database_sha256"]:
        raise RuntimeError("Database backup checksum mismatch")
    name = "scos-recovery-" + uuid4().hex[:16]
    started = time.monotonic()
    docker(
        [
            "run",
            "--detach",
            "--rm",
            "--network",
            "none",
            "--name",
            name,
            "--env",
            "POSTGRES_HOST_AUTH_METHOD=trust",
            IMAGE,
        ]
    )
    try:
        for _ in range(100):
            status = subprocess.run(["docker", "exec", name, "pg_isready", "-U", "postgres"], capture_output=True)
            if status.returncode == 0:
                break
            time.sleep(0.2)
        else:
            raise RuntimeError("Recovery PostgreSQL did not start")
        role = config.DATABASE_SCHEMA + "_app"
        if not re.fullmatch(r"scos_staging_app", role):
            raise RuntimeError("Unexpected recovery role")
        docker(
            ["exec", "-i", name, "psql", "-X", "-v", "ON_ERROR_STOP=1", "-U", "postgres"],
            data=("CREATE ROLE " + role + " NOLOGIN;\n").encode(),
        )
        docker(
            [
                "exec",
                "-i",
                name,
                "pg_restore",
                "--exit-on-error",
                "--no-owner",
                "--no-acl",
                "-U",
                "postgres",
                "-d",
                "postgres",
            ],
            data=dump,
        )
        checks = []
        for table, expected in manifest["tables"].items():
            if not re.fullmatch(r"[a-z_][a-z0-9_]*", table):
                raise RuntimeError("Invalid backup table name")
            query = f'SELECT row_to_json(t) FROM "{config.DATABASE_SCHEMA}"."{table}" t;'
            raw = docker(
                ["exec", "-i", name, "psql", "-X", "-A", "-t", "-v", "ON_ERROR_STOP=1", "-U", "postgres"],
                data=query.encode(),
            )
            rows = sorted(
                json.dumps(json.loads(row), sort_keys=True, separators=(",", ":"))
                for row in raw.decode().splitlines()
                if row
            )
            if {"rows": len(rows), "sha256": sha(rows)} != expected:
                raise RuntimeError("Recovery table checksum mismatch: " + table)
            checks.append(table)
        total = 0
        with tempfile.TemporaryDirectory(prefix="scos-recovered-media-") as temporary:
            for item in manifest["objects"]:
                storage.safe_key(item["key"])
                data = decrypt((folder / (item["key"] + ".enc")).read_bytes(), key, label + ":" + item["key"])
                target = Path(temporary) / item["key"]
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
                target.chmod(0o600)
                if sha(target.read_bytes()) != item["sha256"] or len(data) != item["bytes"]:
                    raise RuntimeError("Recovery media checksum mismatch")
                total += len(data)
        return {
            "status": "passed",
            "tables_verified": len(checks),
            "objects_restored": len(manifest["objects"]),
            "media_bytes_restored": total,
            "seconds": round(time.monotonic() - started, 2),
            "isolation": "New PostgreSQL container, no network, no exposed ports, no worker. Removed after verification.",
            "scope": "Private app schema and media bytes; Supabase Auth configuration and a regional failover were not restored.",
        }
    finally:
        docker(["rm", "--force", "--volumes", name])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--restore-drill", action="store_true")
    parser.add_argument(
        "--restore-from",
        type=Path,
        help="Verify an existing encrypted archive without contacting the source database or Storage",
    )
    args = parser.parse_args()
    config.validate()
    if config.ENV != "staging" or config.DATA_PROVIDER != "supabase" or config.DATABASE_SCHEMA != "scos_staging":
        raise RuntimeError("This operator tool is restricted to the isolated Supabase staging schema")
    key = key_from_env()
    if args.restore_from:
        folder = args.restore_from.resolve()
        label = config.SUPABASE_REF + ":" + config.DATABASE_SCHEMA + ":" + folder.name
        print(json.dumps(restore_drill(folder, key, label), indent=2))
        return
    if not args.output:
        parser.error("--output is required when creating a backup")
    folder = args.output.resolve() / now().strftime("%Y%m%dT%H%M%SZ")
    folder.mkdir(parents=True, mode=0o700)
    folder.chmod(0o700)
    label = config.SUPABASE_REF + ":" + config.DATABASE_SCHEMA + ":" + folder.name

    def save(name, data):
        path = folder / name
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        path.write_bytes(data)
        path.chmod(0o600)

    with connect() as c:
        c.execute("BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
        snapshot = c.execute("SELECT pg_export_snapshot() AS id").fetchone()["id"]
        tables, refs = table_manifest(c, config.DATABASE_SCHEMA), referenced_objects(c)
        dump = dump_database(snapshot)
    save("database.enc", encrypt(dump, key, label + ":database"))
    objects = []
    inventory = object_inventory()
    if not refs <= set(inventory):
        raise RuntimeError("Referenced media is missing from Storage; backup is incomplete")
    for name in inventory:
        data = storage.read(name)
        objects.append({"key": name, "sha256": sha(data), "bytes": len(data)})
        save(name + ".enc", encrypt(data, key, label + ":" + name))
    manifest = {
        "project_ref": config.SUPABASE_REF,
        "schema": config.DATABASE_SCHEMA,
        "created_at": now(),
        "database_sha256": sha(dump),
        "tables": tables,
        "objects": objects,
        "excluded": ["hosted_owner_policy data", "Supabase Auth schema and provider credentials"],
    }
    save("manifest.enc", encrypt(json.dumps(clean(manifest)).encode(), key, label + ":manifest"))
    report = {
        "status": "backup_created",
        "encrypted": True,
        "project_ref": config.SUPABASE_REF,
        "tables": len(tables),
        "media_objects": len(objects),
        "media_bytes": sum(o["bytes"] for o in objects),
    }
    if args.restore_drill:
        report["restore_drill"] = restore_drill(folder, key, label)
    save("REPORT.json", json.dumps(report, indent=2).encode())
    print(json.dumps({**report, "encrypted_backup_folder": str(folder)}, indent=2))


if __name__ == "__main__":
    main()
