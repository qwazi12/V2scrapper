"""Manual staging smoke: real Linux media, PostgreSQL revision and durable private S3.

Run inside the isolated Railway worker. Creates only clearly synthetic test objects;
does not create an owner, a session, a campaign or a publication attempt.
"""

import json
from uuid import uuid4

from scos import config, storage
from scos.db import connect, one
from scos.media import render


def main():
    config.validate()
    if config.ENV != "staging":
        raise RuntimeError("This smoke test is restricted to isolated staging")
    with connect() as c:
        revision = one(c, "SELECT version_num FROM alembic_version")["version_num"]
        database = one(c, "SELECT current_database() AS name")["name"]
    if revision != "scos_0003" or database != "scos_staging":
        raise RuntimeError("Staging migrations have not reached the expected revision")
    storage.init()
    output, checks = render(
        config.RUNTIME / "staging-smoke" / str(uuid4()),
        {"format": "short_9_16", "config": {"fixture": True}},
        {"title": "Isolated staging verification"},
        {
            "sentences": [
                {"text": "This original fictional scene verifies the isolated rendering service."},
                {"text": "The test creates synthetic media and never publishes to a social account."},
                {"text": "Private object storage preserves the verified export beyond this container."},
            ]
        },
    )
    failed = [name for name, status, _ in checks if status == "fail"]
    if failed:
        raise RuntimeError("Media QA failed: " + ", ".join(failed))
    data = storage.read(output["object_key"], output["sha256"])
    print(
        json.dumps(
            {
                "environment": config.ENV,
                "database": database,
                "migration": revision,
                "object_key": output["object_key"],
                "sha256": output["sha256"],
                "bytes_read_from_s3": len(data),
                "checks": checks,
                "synthetic": True,
                "published": False,
                "owner_auth_bypassed": False,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
