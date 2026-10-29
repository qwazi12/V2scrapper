import pytest
from scos.db import one, all_rows, insert, now
from scos.config import OWNER_ID
from scos.commands import command
from scos.policy import PolicyError, export_ready, claim_errors, variant_ready
from helpers import ready_campaign, upstream_test_export


def test_claim_correction_revokes_research_scripts_and_exports(conn):
    _, variants = ready_campaign(conn)
    ex = upstream_test_export(conn, variants[0])
    claim = one(conn, "SELECT * FROM claims LIMIT 1")
    changed = command(
        conn,
        "claim.edit",
        claim["id"],
        {
            "expected_revision": claim["revision"],
            "text": "A corrected statement requires new evidence.",
            "review_note": "The original interpretation was not supported by the passage.",
        },
        OWNER_ID,
    )
    assert changed["revision"] == claim["revision"] + 1
    assert changed["factual_value"] == {} and changed["status"] == "evidence_pending"
    assert one(conn, "SELECT status FROM exports WHERE id=%s", (ex["id"],))["status"] == "revoked"
    assert all(s["review_status"] == "revoked" for s in all_rows(conn, "SELECT * FROM scripts"))
    assert (
        one(
            conn,
            "SELECT count(*) AS n FROM claim_evidence WHERE claim_id=%s AND reviewed_at IS NOT NULL",
            (claim["id"],),
        )["n"]
        == 0
    )
    with pytest.raises(PolicyError):
        export_ready(conn, ex["id"])
    assert (
        one(conn, "SELECT details FROM audit_events WHERE action='claim.revised'")["details"]["before"]["text"]
        == claim["text"]
    )


def test_source_invalidation_retains_snapshot_but_revokes_dependencies(conn):
    campaign, variants = ready_campaign(conn)
    ex = upstream_test_export(conn, variants[0])
    source = one(conn, "SELECT * FROM source_records LIMIT 1")
    command(
        conn,
        "source.invalidate",
        source["id"],
        {
            "expected_hash": source["content_sha256"],
            "review_note": "The source is no longer current and needs replacement.",
        },
        OWNER_ID,
    )
    updated = one(conn, "SELECT * FROM source_records WHERE id=%s", (source["id"],))
    assert updated["snippet"] == source["snippet"] and updated["content_sha256"] == source["content_sha256"]
    assert updated["fetch_status"] == "invalidated"
    assert one(conn, "SELECT status FROM exports WHERE id=%s", (ex["id"],))["status"] == "revoked"
    with pytest.raises(PolicyError):
        command(conn, "research.approve", campaign["opportunity_id"], {}, OWNER_ID)


def test_evidence_conflict_remains_visible_and_blocks_approval(conn):
    campaign, _ = ready_campaign(conn)
    evidence = one(conn, "SELECT e.*,cl.revision FROM claim_evidence e JOIN claims cl ON cl.id=e.claim_id LIMIT 1")
    command(
        conn,
        "evidence.adjudicate",
        evidence["id"],
        {
            "expected_revision": evidence["revision"],
            "stance": "contradicts",
            "review_note": "The passage contradicts the claim's intended interpretation.",
        },
        OWNER_ID,
    )
    assert any("contradictory" in error for error in claim_errors(conn, evidence["claim_id"]))
    with pytest.raises(PolicyError):
        command(conn, "research.approve", campaign["opportunity_id"], {}, OWNER_ID)


def test_script_restore_creates_new_draft_without_changing_prior_wording(conn):
    _, variants = ready_campaign(conn)
    variant = variants[0]
    initial = one(conn, "SELECT * FROM scripts WHERE variant_id=%s", (variant["id"],))
    command(
        conn,
        "script.save",
        variant["id"],
        {
            "expected_revision": 1,
            "sentences": [
                {"sentence_id": "s1", "text": "An alternate editorial opening.", "kind": "editorial", "claim_refs": []}
            ],
        },
        OWNER_ID,
    )
    restored = command(conn, "script.restore", variant["id"], {"expected_revision": 2, "source_revision": 1}, OWNER_ID)
    assert restored["revision"] == 3 and restored["review_status"] == "draft"
    assert restored["text"] == initial["text"] and restored["sentences"] == initial["sentences"]
    assert one(conn, "SELECT text FROM scripts WHERE id=%s", (initial["id"],))["text"] == initial["text"]
    with pytest.raises(PolicyError):
        command(conn, "script.restore", variant["id"], {"expected_revision": 2, "source_revision": 1}, OWNER_ID)


def test_rights_revocation_invalidates_all_asset_uses(conn):
    _, variants = ready_campaign(conn)
    ex = upstream_test_export(conn, variants[0])
    asset = one(conn, "SELECT * FROM media_assets LIMIT 1")
    command(
        conn,
        "asset.revoke_rights",
        asset["id"],
        {"review_note": "The owner has withdrawn permission for further use."},
        OWNER_ID,
    )
    assert one(conn, "SELECT status FROM media_assets WHERE id=%s", (asset["id"],))["status"] == "restricted"
    assert all(
        r["reviewed_at"] is None for r in all_rows(conn, "SELECT * FROM asset_rights WHERE asset_id=%s", (asset["id"],))
    )
    assert one(conn, "SELECT status FROM exports WHERE id=%s", (ex["id"],))["status"] == "revoked"
    for variant in variants:
        with pytest.raises(PolicyError):
            variant_ready(conn, variant["id"])


def test_license_scope_changes_cannot_reuse_export_approval(conn):
    _, variants = ready_campaign(conn)
    ex = upstream_test_export(conn, variants[0])
    conn.execute("UPDATE asset_rights SET permitted_uses=ARRAY['render']")
    with pytest.raises(PolicyError) as error:
        export_ready(conn, ex["id"])
    assert error.value.code == "EXPORT_APPROVAL_STALE"


def test_future_license_is_not_active(conn):
    _, variants = ready_campaign(conn)
    conn.execute("UPDATE asset_rights SET valid_from=now()+interval '1 day'")
    with pytest.raises(PolicyError) as error:
        variant_ready(conn, variants[0]["id"])
    assert error.value.code == "ASSET_UNLICENSED"


def test_missing_structured_values_cannot_match_as_null(conn):
    source = insert(
        conn,
        "source_records",
        provider="fixture",
        uri="https://example.invalid/credit",
        snippet="A structured credit is unavailable.",
        metadata={},
    )
    claim = insert(
        conn,
        "claims",
        text="An unproven credit.",
        kind="writer_credit",
        epistemic_type="fact",
        factual_value={"identity_resolved": True},
    )
    insert(
        conn,
        "claim_evidence",
        claim_id=claim["id"],
        source_id=source["id"],
        stance="supports",
        locator="credit",
        excerpt=source["snippet"],
        structured_field="screenplay",
        reviewed_at=now(),
        reviewer_user_id=OWNER_ID,
    )
    assert any("Structured" in error for error in claim_errors(conn, claim["id"]))
