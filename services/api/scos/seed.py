from datetime import timedelta
from .db import one, insert, sha, now, audit
from .config import OWNER_ID, RUNTIME
from . import storage


def bootstrap(c):
    c.execute(
        """INSERT INTO app_users(id,email,display_name,auth_subject) VALUES(%s,'owner@scos.local','Screen Central','scos-local-owner')
        ON CONFLICT(id) DO NOTHING""",
        (OWNER_ID,),
    )
    for platform in ("youtube", "instagram", "facebook"):
        c.execute(
            """INSERT INTO social_accounts(platform,external_account_id,display_name,handle,capability_snapshot)
            VALUES(%s,%s,%s,%s,%s::jsonb) ON CONFLICT(platform,external_account_id) DO NOTHING""",
            (
                platform,
                "scos-mock-" + platform,
                "Screen Central · mock",
                "@screencentral",
                '{"mode":"mock","live":"requires_connection","can_upload_video":false}',
            ),
        )
    c.execute(
        "INSERT INTO budget_policies(policy_key,period,limit_amount) VALUES('scos-local-daily','daily',0) ON CONFLICT DO NOTHING"
    )


def create_fixture(c, actor):
    bootstrap(c)
    existing = one(c, "SELECT * FROM opportunities WHERE dedupe_fingerprint='scos-lighthouse-fixture-v1'")
    if existing:
        return {"opportunity_id": str(existing["id"]), "already_exists": True}
    opportunity = insert(
        c,
        "opportunities",
        title="The Last Lighthouse: why the final light matters",
        angle="A fictional story about memory, built entirely from original test material.",
        audience_hypothesis="Fans of intimate science fiction and character-led endings",
        payoff="Understand the visual metaphor without a generic recap",
        why_us="An original, source-linked interpretation with native treatments for each format.",
        status="research_pending",
        dedupe_fingerprint="scos-lighthouse-fixture-v1",
        rationale={
            "why_now": "Local workflow validation; no live trend claim",
            "counterevidence": "Fictional sample. No measured audience demand.",
            "source": "Owner-created synthetic press notes",
            "cost_to_try": "$0 external; local compute only",
            "demand": None,
            "confidence": "unknown",
        },
    )
    source = insert(
        c,
        "source_records",
        provider="fixture",
        uri="https://example.invalid/scos/the-last-lighthouse",
        source_kind="original_fixture",
        trust_class="owner_created",
        title="The Last Lighthouse · original fictional press notes",
        snippet="Mara keeps the last lighthouse lit. The signal guides travelers home. The final light represents a promise.",
        content_sha256=sha(
            b"Mara keeps the last lighthouse lit. The signal guides travelers home. The final light represents a promise."
        ),
        rights_to_store="owner_created",
        expires_at=now() + timedelta(days=90),
        metadata={"fixture": True, "entity_id": "scos-fiction-lighthouse"},
    )
    for i, text in enumerate(["Mara keeps the last lighthouse lit.", "The signal guides travelers home."]):
        claim = insert(
            c,
            "claims",
            opportunity_id=opportunity["id"],
            text=text,
            kind="story_fact",
            epistemic_type="fact",
            status="evidence_pending",
            factual_value={"identity_resolved": True, "entity": "scos-fiction-lighthouse"},
        )
        insert(
            c,
            "claim_evidence",
            claim_id=claim["id"],
            source_id=source["id"],
            stance="supports",
            locator=f"press_notes.sentence.{i + 1}",
            excerpt=text,
            evidence_scope="exact_statement",
            review_method="owner_fixture_review",
        )
    from .media import card

    asset_path = RUNTIME / "fixture.png"
    card(asset_path, (1920, 1080), "The Last Lighthouse", "An original fictional world.", 0)
    key, digest, byte_size = storage.put(asset_path)
    asset = insert(
        c,
        "media_assets",
        kind="image",
        origin_type="owner_created_fixture",
        filename="lighthouse-original.png",
        media_type="image/png",
        sha256=digest,
        byte_size=byte_size,
        object_key=key,
        width=1920,
        height=1080,
        status="approved",
        metadata={"fixture": True, "provenance": "Generated locally by scos.media.card; no third-party content"},
    )
    proof = RUNTIME / "rights-proof.txt"
    proof.write_text(
        "Original geometric artwork generated locally by Screen Central OS. Synthetic test use only. No third-party audiovisual content."
    )
    proof_key, _, _ = storage.put(proof)
    insert(
        c,
        "asset_rights",
        asset_id=asset["id"],
        rights_kind="owner_created",
        rights_holder="Screen Central local fixture",
        proof_object_key=proof_key,
        platforms=["youtube", "instagram", "facebook"],
        permitted_uses=["render", "test_publish"],
        derivatives_allowed=True,
        monetization_allowed=False,
        territory="worldwide",
        reviewed_by=actor,
        reviewed_at=now(),
        notes="Original synthetic test art; not a commercial asset attestation",
    )
    audit(c, "fixture.created", opportunity["id"], actor, details={"synthetic": True})
    return {"opportunity_id": str(opportunity["id"]), "source_id": str(source["id"])}
