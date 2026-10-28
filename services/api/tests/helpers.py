from scos.seed import create_fixture
from scos.db import all_rows, one, insert
from scos.config import OWNER_ID, RUNTIME
from scos.commands import command
from scos import storage


def ready_campaign(c):
    fixture = create_fixture(c, OWNER_ID)
    for claim in all_rows(c, "SELECT * FROM claims WHERE opportunity_id=%s", (fixture["opportunity_id"],)):
        command(
            c,
            "claim.review",
            claim["id"],
            {"expected_revision": claim["revision"], "review_note": "Exact original fixture evidence reviewed"},
            OWNER_ID,
        )
    command(c, "research.approve", fixture["opportunity_id"], {}, OWNER_ID)
    campaign = command(c, "campaign.create", fixture["opportunity_id"], {}, OWNER_ID)
    variants = all_rows(c, "SELECT * FROM campaign_variants WHERE campaign_id=%s ORDER BY format", (campaign["id"],))
    for variant in variants:
        script = one(c, "SELECT * FROM scripts WHERE variant_id=%s", (variant["id"],))
        command(
            c,
            "script.approve",
            variant["id"],
            {"expected_revision": script["revision"], "expected_hash": script["text_sha256"]},
            OWNER_ID,
        )
    return campaign, variants


def upstream_test_export(c, variant):
    # Unit/fault fixture only: substitutes upstream renderer; real render is independently tested in test_media.
    from scos.policy import variant_ready

    _, _, _, _, snapshot = variant_ready(c, variant["id"])
    path = RUNTIME / "test-upstream.bin"
    path.write_bytes(b"isolated-test-upstream-render-output-" + str(variant["id"]).encode())
    key, digest, size = storage.put(path)
    ex = insert(
        c,
        "exports",
        variant_id=variant["id"],
        format=variant["format"],
        object_key=key,
        sha256=digest,
        byte_size=size,
        input_snapshot_hash=snapshot,
        status="qa_passed",
        width=1920,
        height=1080,
    )
    insert(
        c,
        "quality_checks",
        export_id=ex["id"],
        check_name="unit_fixture_upstream",
        severity="blocker",
        status="pass",
        checker_version="test-only",
    )
    command(
        c,
        "export.approve",
        ex["id"],
        {"expected_hash": digest, "review_note": "Unit fixture; not a production media approval"},
        OWNER_ID,
    )
    return ex
