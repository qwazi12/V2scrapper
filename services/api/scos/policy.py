from datetime import datetime, timezone
from .db import one, all_rows, sha


class PolicyError(Exception):
    def __init__(self, code, message, status=409):
        self.code, self.message, self.status = code, message, status


def require(condition, code, message, status=409):
    if not condition:
        raise PolicyError(code, message, status)


def claim_errors(c, claim_id):
    claim = one(c, "SELECT * FROM claims WHERE id=%s", (claim_id,))
    if not claim:
        return ["Claim does not exist"]
    if claim["epistemic_type"] == "opinion":
        return []
    evidence = all_rows(
        c,
        """SELECT e.*, s.expires_at, s.fetch_status, s.metadata, s.snippet FROM claim_evidence e
        JOIN source_records s ON s.id=e.source_id WHERE e.claim_id=%s""",
        (claim_id,),
    )
    errors = []
    if any(e["stance"] == "contradicts" for e in evidence):
        errors.append("Unresolved contradictory evidence")
    supporting = [
        e
        for e in evidence
        if e["stance"] == "supports"
        and e["reviewed_at"]
        and e["locator"].strip()
        and e["excerpt"]
        and e["excerpt"] in (e["snippet"] or "")
        and (not e["expires_at"] or e["expires_at"] > datetime.now(timezone.utc))
        and e["fetch_status"] == "ok"
    ]
    if not supporting:
        errors.append("Exact, reviewed and fresh supporting passage required")
    value = claim["factual_value"] or {}
    if not value.get("identity_resolved"):
        errors.append("Canonical identity unresolved")
    if claim["kind"] in ("cast_credit", "writer_credit", "release_date", "streaming", "box_office"):
        matching = [
            e
            for e in supporting
            if e["structured_field"] and e["metadata"].get(e["structured_field"]) == value.get("expected")
        ]
        if not matching:
            errors.append("Structured field does not match this claim")
    return errors


def research_ready(c, package_id):
    pack = one(c, "SELECT * FROM research_packages WHERE id=%s", (package_id,))
    require(pack and pack["status"] == "approved", "CLAIM_UNVERIFIED", "Research package needs owner approval")
    for cid in pack["claim_ids"]:
        claim = one(c, "SELECT * FROM claims WHERE id=%s", (cid,))
        require(
            claim and claim["status"] == "supported" and not claim_errors(c, cid),
            "CLAIM_UNVERIFIED",
            "Research has unsupported, stale or contradictory claims",
        )
    return pack


def variant_ready(c, variant_id):
    variant = one(c, "SELECT * FROM campaign_variants WHERE id=%s", (variant_id,))
    require(variant, "NOT_FOUND", "Variant not found", 404)
    campaign = one(c, "SELECT * FROM campaigns WHERE id=%s", (variant["campaign_id"],))
    pack = research_ready(c, campaign["research_package_id"])
    script = one(c, "SELECT * FROM scripts WHERE variant_id=%s ORDER BY revision DESC LIMIT 1", (variant_id,))
    require(
        script and script["review_status"] == "owner_approved", "CLAIM_UNVERIFIED", "Approve the current script first"
    )
    for sentence in script["sentences"]:
        require(
            sentence.get("kind") in ("factual", "editorial", "transition"),
            "CLAIM_UNVERIFIED",
            "Sentence verdict missing",
        )
        if sentence["kind"] == "factual":
            refs = sentence.get("claim_refs", [])
            require(refs, "CLAIM_UNVERIFIED", "A factual sentence has no citations")
            for cid in refs:
                require(
                    str(cid) in [str(x) for x in pack["claim_ids"]],
                    "CLAIM_UNVERIFIED",
                    "Citation is outside this research package",
                )
                claim = one(c, "SELECT * FROM claims WHERE id=%s", (cid,))
                require(
                    claim and claim["status"] == "supported" and not claim_errors(c, cid),
                    "CLAIM_UNVERIFIED",
                    "A script citation no longer passes review",
                )
            # Initial deterministic profile allows exact approved statements only; no semantic LLM verification.
            cited_text = [one(c, "SELECT text FROM claims WHERE id=%s", (cid,))["text"] for cid in refs]
            require(
                sentence["text"] in cited_text,
                "CLAIM_UNVERIFIED",
                "Factual sentence must match an approved atomic claim",
            )
    assets = all_rows(
        c,
        """SELECT a.*, r.id AS rights_id,r.rights_kind,r.valid_to,r.platforms,r.permitted_uses,
        r.derivatives_allowed,r.reviewed_at,r.proof_object_key FROM asset_usage u JOIN media_assets a ON a.id=u.asset_id
        JOIN asset_rights r ON r.id=u.rights_id WHERE u.variant_id=%s""",
        (variant_id,),
    )
    require(assets, "ASSET_UNLICENSED", "Select at least one approved original asset")
    for a in assets:
        require(
            a["status"] == "approved"
            and a["rights_kind"] in ("owner_created", "licensed", "provider_permitted")
            and a["reviewed_at"]
            and a["proof_object_key"]
            and a["derivatives_allowed"]
            and "render" in a["permitted_uses"],
            "ASSET_UNLICENSED",
            "Asset lacks reviewed derivative and render rights",
        )
        require(
            not a["valid_to"] or a["valid_to"] > datetime.now(timezone.utc),
            "ASSET_EXPIRED",
            "Asset license has expired",
        )
    snapshot = sha(
        {
            "campaign": str(campaign["id"]),
            "revision": campaign["revision"],
            "research": pack["content_hash"],
            "script": script["text_sha256"],
            "format": variant["format"],
            "config": variant["config"],
            "assets": [
                {
                    "id": str(a["id"]),
                    "sha": a["sha256"],
                    "rights": str(a["rights_id"]),
                    "expires": a["valid_to"],
                    "platforms": a["platforms"],
                }
                for a in assets
            ],
        }
    )
    return variant, campaign, script, assets, snapshot


def export_ready(c, export_id, approved=True, platform=None):
    export = one(c, "SELECT * FROM exports WHERE id=%s", (export_id,))
    require(export, "NOT_FOUND", "Export not found", 404)
    variant, campaign, script, assets, snapshot = variant_ready(c, export["variant_id"])
    require(
        snapshot == export["input_snapshot_hash"],
        "EXPORT_APPROVAL_STALE",
        "Inputs changed. Render and review a new export.",
    )
    from .storage import read

    try:
        read(export["object_key"], export["sha256"])
    except ValueError:
        raise PolicyError("ASSET_MISMATCH", "Export bytes do not match the immutable hash")
    if platform:
        require(
            all(platform in a["platforms"] for a in assets),
            "ASSET_UNLICENSED",
            "Asset license does not cover destination platform",
        )
    checks = all_rows(c, "SELECT * FROM quality_checks WHERE export_id=%s", (export_id,))
    require(
        checks and not any(q["severity"] == "blocker" and q["status"] != "pass" for q in checks),
        "MEDIA_QA_FAILED",
        "Blocking quality checks must pass",
    )
    if approved:
        approval = one(
            c,
            """SELECT * FROM export_approvals WHERE export_id=%s AND export_sha256=%s
          AND input_snapshot_hash=%s AND status='approved' AND approval_kind='publish_ready' """,
            (export_id, export["sha256"], snapshot),
        )
        require(approval and export["status"] == "approved", "EXPORT_APPROVAL_STALE", "Approve this exact export first")
    return export
