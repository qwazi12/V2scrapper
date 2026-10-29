from datetime import timedelta
from decimal import Decimal
from uuid import UUID
from psycopg.types.json import Jsonb
from .db import one, all_rows, insert, sha, now, audit, event
from .policy import require, claim_errors, research_ready, variant_ready, export_ready, PolicyError
from .seed import create_fixture
from .config import ENV, NAMESPACE


def invalidate(c, opportunity_id, actor):
    c.execute(
        "UPDATE research_packages SET status='revoked' WHERE opportunity_id=%s AND status='approved'", (opportunity_id,)
    )
    variants = all_rows(
        c,
        """SELECT v.id FROM campaign_variants v JOIN campaigns ca ON ca.id=v.campaign_id
        WHERE ca.opportunity_id=%s""",
        (opportunity_id,),
    )
    for v in variants:
        c.execute(
            "UPDATE scripts SET review_status='revoked' WHERE variant_id=%s AND review_status='owner_approved'",
            (v["id"],),
        )
        revoke_variant(c, v["id"], actor)


def revoke_variant(c, variant_id, actor):
    exports = all_rows(c, "SELECT id FROM exports WHERE variant_id=%s", (variant_id,))
    for ex in exports:
        c.execute("UPDATE export_approvals SET status='revoked',revoked_at=now() WHERE export_id=%s", (ex["id"],))
        c.execute("UPDATE exports SET status='revoked' WHERE id=%s", (ex["id"],))
        c.execute("UPDATE platform_packages SET status='revoked' WHERE export_id=%s", (ex["id"],))
        c.execute(
            "UPDATE publication_attempts SET state='cancelled',error_code='EXPORT_APPROVAL_STALE' WHERE export_id=%s AND state IN ('draft','scheduled','claimed')",
            (ex["id"],),
        )
    audit(c, "variant.dependencies_changed", variant_id, actor)


def command(c, action, target, p, actor):
    if action == "asset.review_rights":
        asset = one(c, "SELECT * FROM media_assets WHERE id=%s FOR UPDATE", (target,))
        require(asset, "NOT_FOUND", "Asset not found", 404)
        require(
            p.get("owner_attestation") is True and len(p.get("review_note", "")) >= 15,
            "ASSET_UNLICENSED",
            "Confirm ownership and provide a specific rights basis",
            422,
        )
        from .config import RUNTIME
        from . import storage

        proof = RUNTIME / ("rights-" + str(target) + ".txt")
        proof.write_text(p["review_note"])
        key, _, _ = storage.put(proof)
        rights = insert(
            c,
            "asset_rights",
            asset_id=target,
            rights_kind="owner_created",
            rights_holder="Owner attestation",
            proof_object_key=key,
            platforms=["youtube", "instagram", "facebook"],
            permitted_uses=["render", "test_publish"],
            derivatives_allowed=True,
            reviewed_by=actor,
            reviewed_at=now(),
            notes=p["review_note"],
        )
        c.execute("UPDATE media_assets SET status='approved' WHERE id=%s", (target,))
        return rights
    if action == "variant.select_asset":
        variant = one(c, "SELECT * FROM campaign_variants WHERE id=%s FOR UPDATE", (target,))
        require(variant, "NOT_FOUND", "Variant not found", 404)
        asset = one(c, "SELECT * FROM media_assets WHERE id=%s AND status='approved'", (p.get("asset_id"),))
        rights = one(
            c, "SELECT * FROM asset_rights WHERE asset_id=%s ORDER BY created_at DESC LIMIT 1", (p.get("asset_id"),)
        )
        require(
            asset and rights and rights["reviewed_at"],
            "ASSET_UNLICENSED",
            "Choose an approved image with reviewed rights",
        )
        revoke_variant(c, target, actor)
        c.execute("DELETE FROM asset_usage WHERE variant_id=%s", (target,))
        insert(
            c,
            "asset_usage",
            variant_id=target,
            asset_id=asset["id"],
            rights_id=rights["id"],
            use_kind="approved_image",
            timeline_end_ms=variant["target_duration_ms"] or 15000,
        )
        c.execute(
            "UPDATE scripts SET review_status='draft' WHERE variant_id=%s AND review_status='owner_approved'", (target,)
        )
        return {"status": "selected", "asset_id": str(asset["id"])}
    if action == "fixture":
        require(ENV != "production", "FORBIDDEN", "Synthetic fixtures are disabled in production", 403)
        return create_fixture(c, actor)
    if action == "opportunity.create":
        require(
            len(p.get("title", "").strip()) >= 5, "INVALID_INPUT", "Provide a title of at least five characters", 422
        )
        return insert(
            c,
            "opportunities",
            title=p["title"].strip(),
            angle=p.get("angle", ""),
            audience_hypothesis=p.get("audience_hypothesis", "Owner-defined audience"),
            why_us=p.get("why_us", "To be researched"),
            rationale={
                "why_now": "Manual candidate",
                "counterevidence": "Research not completed",
                "demand": None,
                "confidence": "unknown",
            },
        )
    if action == "opportunity.decide":
        require(
            p.get("decision") in ("rejected", "deferred", "research_pending"), "INVALID_INPUT", "Invalid decision", 422
        )
        require(len(p.get("reason", "")) >= 3, "INVALID_INPUT", "A decision reason is required", 422)
        row = one(
            c,
            "UPDATE opportunities SET status=%s,owner_decision=%s,owner_decision_at=now(),revision=revision+1 WHERE id=%s RETURNING *",
            (p["decision"], p["reason"], target),
        )
        require(row, "NOT_FOUND", "Opportunity not found", 404)
        return row
    if action == "source.attach":
        opp = one(c, "SELECT * FROM opportunities WHERE id=%s", (target,))
        require(opp, "NOT_FOUND", "Opportunity not found", 404)
        text = p.get("excerpt", "").strip()
        require(
            10 <= len(text) <= 4000, "INVALID_INPUT", "Provide a permitted excerpt between 10 and 4000 characters", 422
        )
        require(
            p.get("url", "").startswith("https://"),
            "SOURCE_FETCH_BLOCKED",
            "Use an HTTPS reference URL. This action stores metadata only.",
            422,
        )
        source = insert(
            c,
            "source_records",
            provider="manual",
            uri=p["url"],
            title=p.get("title", "Owner-supplied excerpt"),
            snippet=text,
            content_sha256=sha(text.encode()),
            source_kind="manual_excerpt",
            trust_class="unclassified",
            rights_to_store="permitted_excerpt",
            expires_at=now() + timedelta(hours=24),
            metadata={"owner_attested_excerpt": True, "not_independently_fetched": True},
        )
        claim = insert(
            c,
            "claims",
            opportunity_id=target,
            text=p.get("claim", text),
            kind="general_fact",
            epistemic_type="fact",
            status="evidence_pending",
            factual_value={"identity_resolved": False},
        )
        insert(
            c,
            "claim_evidence",
            claim_id=claim["id"],
            source_id=source["id"],
            stance="supports",
            locator=p.get("locator", "owner_supplied_excerpt"),
            excerpt=text,
        )
        return {"source": source, "claim": claim}
    if action == "claim.review":
        claim = one(c, "SELECT * FROM claims WHERE id=%s FOR UPDATE", (target,))
        require(claim, "NOT_FOUND", "Claim not found", 404)
        require(
            p.get("expected_revision") == claim["revision"], "CONFLICT_REVISION", "Claim changed; reload before review"
        )
        require(len(p.get("review_note", "")) >= 3, "INVALID_INPUT", "Write a review note", 422)
        if p.get("resolve_identity"):
            value = claim["factual_value"] or {}
            value["identity_resolved"] = True
            c.execute("UPDATE claims SET factual_value=%s WHERE id=%s", (Jsonb(value), target))
        c.execute(
            "UPDATE claim_evidence SET reviewed_at=now(),reviewer_user_id=%s,notes=%s WHERE claim_id=%s",
            (actor, p["review_note"], target),
        )
        errors = claim_errors(c, target)
        status = "contradicted" if any("contradictory" in e for e in errors) else "uncertain" if errors else "supported"
        invalidate(c, claim["opportunity_id"], actor)
        result = one(
            c,
            "UPDATE claims SET status=%s,revision=revision+1,last_adjudicated_at=now() WHERE id=%s RETURNING *",
            (status, target),
        )
        event(c, "claim.adjudicated", target, result["revision"], status=status)
        return {"claim": result, "blocking_reasons": errors}
    if action == "research.approve":
        claims = all_rows(c, "SELECT * FROM claims WHERE opportunity_id=%s ORDER BY created_at,id", (target,))
        require(claims, "CLAIM_UNVERIFIED", "Add claims and exact source evidence first")
        errors = [e for cl in claims for e in claim_errors(c, cl["id"]) if cl["epistemic_type"] != "opinion"]
        require(
            not errors and all(cl["status"] == "supported" for cl in claims),
            "CLAIM_UNVERIFIED",
            "; ".join(errors) or "Review every claim first",
        )
        ids = [cl["id"] for cl in claims]
        sources = all_rows(c, "SELECT DISTINCT source_id FROM claim_evidence WHERE claim_id=ANY(%s)", (ids,))
        digest = sha(claims)
        existing = one(c, "SELECT * FROM research_packages WHERE content_hash=%s", (digest,))
        if existing and existing["status"] == "approved":
            return existing
        revision = one(
            c,
            "SELECT coalesce(max(revision),0)+1 AS revision FROM research_packages WHERE opportunity_id=%s",
            (target,),
        )["revision"]
        pack = insert(
            c,
            "research_packages",
            opportunity_id=target,
            revision=revision,
            claim_ids=ids,
            source_ids=[s["source_id"] for s in sources],
            policy_version="scos-human-exact-v1",
            summary="Owner reviewed exact evidence locators and canonical identities.",
            content_hash=digest,
            status="approved",
            approved_by=actor,
            approved_at=now(),
        )
        c.execute("UPDATE opportunities SET status='accepted',revision=revision+1 WHERE id=%s", (target,))
        event(c, "research.approved", pack["id"], content_hash=digest)
        return pack
    if action == "campaign.create":
        pack = one(
            c,
            "SELECT * FROM research_packages WHERE opportunity_id=%s AND status='approved' ORDER BY revision DESC LIMIT 1",
            (target,),
        )
        require(pack, "CLAIM_UNVERIFIED", "Approve research before creating a campaign")
        research_ready(c, pack["id"])
        opp = one(c, "SELECT * FROM opportunities WHERE id=%s", (target,))
        existing = one(c, "SELECT * FROM campaigns WHERE research_package_id=%s", (pack["id"],))
        if existing:
            return existing
        campaign = insert(
            c,
            "campaigns",
            opportunity_id=target,
            research_package_id=pack["id"],
            title=opp["title"],
            series_name="Moments Explained",
            viewer_promise=opp["payoff"] or opp["title"],
            original_angle=opp["angle"] or opp["title"],
            status="brief_approved",
            created_by=actor,
        )
        claims = all_rows(c, "SELECT * FROM claims WHERE id=ANY(%s) ORDER BY created_at,id", (pack["claim_ids"],))
        asset = one(
            c,
            "SELECT a.id,r.id AS rights_id FROM media_assets a JOIN asset_rights r ON r.asset_id=a.id WHERE a.origin_type='owner_created_fixture' LIMIT 1",
        )
        for format_, angle in [
            ("long_16_9", "A patient, landscape reading of the original story."),
            ("short_9_16", "One visual idea, an immediate portrait hook."),
            ("carousel_4_5", "Three readable cards, one argument."),
        ]:
            variant = insert(
                c,
                "campaign_variants",
                campaign_id=campaign["id"],
                format=format_,
                angle=angle,
                intended_platform="instagram" if format_ == "carousel_4_5" else "youtube",
                target_duration_ms=15000,
                config={
                    "template_version": "scos-original-v1",
                    "fixture": opp.get("dedupe_fingerprint") == "scos-lighthouse-fixture-v1",
                },
                status="draft",
            )
            sentences = [
                {
                    "sentence_id": f"s{i + 1}",
                    "text": cl["text"],
                    "kind": "factual",
                    "claim_refs": [str(cl["id"])],
                    "beat_index": i,
                }
                for i, cl in enumerate(claims)
            ]
            sentences.append(
                {
                    "sentence_id": "editorial-end",
                    "text": "A promise is worth keeping.",
                    "kind": "editorial",
                    "claim_refs": [],
                    "beat_index": len(sentences),
                }
            )
            if format_ == "long_16_9":
                sentences.insert(
                    0,
                    {
                        "sentence_id": "landscape-hook",
                        "text": "What makes a light worth keeping?",
                        "kind": "editorial",
                        "claim_refs": [],
                        "beat_index": 0,
                    },
                )
                sentences[-1]["text"] = "The power of this fictional ending is its quiet promise."
            elif format_ == "short_9_16":
                sentences = [
                    {
                        "sentence_id": "short-hook",
                        "text": "One light. One promise.",
                        "kind": "editorial",
                        "claim_refs": [],
                        "beat_index": 0,
                    },
                    next(s for s in sentences if s["text"].startswith("Mara")),
                    {
                        "sentence_id": "short-payoff",
                        "text": "That is what makes this fictional ending linger.",
                        "kind": "editorial",
                        "claim_refs": [],
                        "beat_index": 2,
                    },
                ]
            text = " ".join(s["text"] for s in sentences)
            insert(
                c,
                "scripts",
                variant_id=variant["id"],
                revision=1,
                text=text,
                sentences=sentences,
                claim_ids=pack["claim_ids"],
                text_sha256=sha(text.encode()),
            )
            if asset:
                insert(
                    c,
                    "asset_usage",
                    variant_id=variant["id"],
                    asset_id=asset["id"],
                    rights_id=asset["rights_id"],
                    use_kind="original_graphic",
                    timeline_end_ms=15000,
                )
        event(c, "campaign.created", campaign["id"], research_package_id=str(pack["id"]))
        return campaign
    if action in ("script.save", "script.approve"):
        variant = one(c, "SELECT * FROM campaign_variants WHERE id=%s FOR UPDATE", (target,))
        require(variant, "NOT_FOUND", "Variant not found", 404)
        script = one(c, "SELECT * FROM scripts WHERE variant_id=%s ORDER BY revision DESC LIMIT 1", (target,))
        require(
            script and p.get("expected_revision") == script["revision"],
            "CONFLICT_REVISION",
            "Script changed; reload the latest revision",
        )
        if action == "script.save":
            sentences = p.get("sentences", [])
            require(
                1 <= len(sentences) <= 6,
                "INVALID_INPUT",
                "Use between one and six sentences in this initial renderer",
                422,
            )
            require(
                all(isinstance(s.get("text"), str) and 1 <= len(s["text"]) <= 250 for s in sentences),
                "INVALID_INPUT",
                "Each sentence must be 1–250 characters",
                422,
            )
            text = " ".join(s["text"] for s in sentences)
            revoke_variant(c, target, actor)
            refs = list({UUID(cid) for s in sentences for cid in s.get("claim_refs", [])})
            return insert(
                c,
                "scripts",
                variant_id=target,
                revision=script["revision"] + 1,
                text=text,
                sentences=sentences,
                claim_ids=refs,
                text_sha256=sha(text.encode()),
            )
        require(p.get("expected_hash") == script["text_sha256"], "CONFLICT_REVISION", "The script hash has changed")
        c.execute(
            "UPDATE scripts SET review_status='owner_approved',approved_by=%s,approved_at=now() WHERE id=%s",
            (actor, script["id"]),
        )
        variant_ready(c, target)  # Rolls back approval if any factual/rights gate fails.
        c.execute("UPDATE campaign_variants SET status='script_approved' WHERE id=%s", (target,))
        return {"status": "owner_approved", "sha256": script["text_sha256"]}
    if action == "render":
        variant, campaign, script, assets, snapshot = variant_ready(c, target)
        c.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s,0))", ("render:" + snapshot,))
        existing = one(
            c,
            "SELECT * FROM jobs WHERE kind='render' AND input_hash=%s AND status NOT IN ('failed','cancelled','dead_letter')",
            (snapshot,),
        )
        if existing:
            return existing
        job = insert(
            c,
            "jobs",
            kind="render",
            aggregate_kind="variant",
            aggregate_id=target,
            input_hash=snapshot,
            payload={"variant_id": str(target), "snapshot_hash": snapshot},
            max_attempts=2,
        )
        c.execute("UPDATE campaigns SET status='producing' WHERE id=%s", (campaign["id"],))
        event(c, "render.requested", job["id"], variant_id=str(target))
        return job
    if action == "job.cancel":
        job = one(c, "SELECT * FROM jobs WHERE id=%s FOR UPDATE", (target,))
        require(
            job
            and (job["status"] in ("queued", "retry_wait") or job["kind"] == "render" and job["status"] == "running"),
            "CONFLICT_REVISION",
            "Cancel a queued job or an active render; an in-flight publication must be reconciled",
        )
        if job["kind"] == "mock_publish":
            c.execute(
                "UPDATE publication_attempts SET state='cancelled' WHERE id=%s AND state='scheduled'",
                (job["aggregate_id"],),
            )
        insert(
            c,
            "job_events",
            job_id=target,
            stage="cancelled",
            event_type="owner_cancelled",
            message="Owner cancelled this job; its lease is revoked.",
        )
        return one(
            c,
            "UPDATE jobs SET status='cancelled',lease_epoch=lease_epoch+1,lease_owner=NULL,lease_expires_at=NULL WHERE id=%s RETURNING *",
            (target,),
        )
    if action == "job.retry":
        job = one(c, "SELECT * FROM jobs WHERE id=%s FOR UPDATE", (target,))
        require(
            job and job["kind"] == "render" and job["status"] in ("failed", "dead_letter", "cancelled"),
            "CONFLICT_REVISION",
            "Only a stopped render can be retried safely",
        )
        require(
            p.get("expected_lease_epoch") == job["lease_epoch"], "CONFLICT_REVISION", "Job changed; reload before retry"
        )
        _, _, _, _, snapshot = variant_ready(c, job["aggregate_id"])
        require(
            snapshot == job["input_hash"],
            "EXPORT_APPROVAL_STALE",
            "Inputs changed; request a new render from the current script",
        )
        return command(c, "render", job["aggregate_id"], {}, actor)
    if action == "export.approve":
        ex = export_ready(c, target, False)
        require(p.get("expected_hash") == ex["sha256"], "EXPORT_APPROVAL_STALE", "The exact export hash is required")
        require(len(p.get("review_note", "")) >= 3, "INVALID_INPUT", "Record an editorial and rights review note", 422)
        existing = one(
            c,
            "SELECT * FROM export_approvals WHERE export_id=%s AND approval_kind='publish_ready' AND status='approved'",
            (target,),
        )
        if not existing:
            existing = insert(
                c,
                "export_approvals",
                export_id=target,
                export_sha256=ex["sha256"],
                input_snapshot_hash=ex["input_snapshot_hash"],
                approval_kind="publish_ready",
                approved_by=actor,
                notes=p["review_note"],
            )
        c.execute("UPDATE exports SET status='approved' WHERE id=%s", (target,))
        event(c, "export.approved", target, sha256=ex["sha256"])
        return existing
    if action == "export.revoke":
        ex = one(c, "SELECT * FROM exports WHERE id=%s", (target,))
        require(ex, "NOT_FOUND", "Export not found", 404)
        revoke_variant(c, ex["variant_id"], actor)
        return {"status": "revoked"}
    if action == "package.create":
        account = one(c, "SELECT * FROM social_accounts WHERE id=%s", (p.get("account_id"),))
        require(account, "NOT_FOUND", "Select a mock destination account", 404)
        ex = export_ready(c, target, platform=account["platform"])
        title = p.get("title", "Screen Central original fictional test")
        caption = p.get("caption", "Original synthetic fixture. Local mock publication only.")
        limit = {"youtube": 5000, "instagram": 2200, "facebook": 63206}[account["platform"]]
        require(
            1 <= len(title) <= 100 and len(caption) <= limit,
            "PACKAGE_INVALID",
            "Title or caption exceeds the destination limit",
            422,
        )
        require(
            ex["format"] != "carousel_4_5" or account["platform"] != "youtube",
            "PACKAGE_INVALID",
            "YouTube video packages require a video export",
        )
        package = insert(
            c,
            "platform_packages",
            export_id=target,
            account_id=account["id"],
            title=title,
            caption=caption,
            alt_text=p.get("alt_text", "Original test story graphic"),
            revision=one(
                c,
                "SELECT coalesce(max(revision),0)+1 AS n FROM platform_packages WHERE export_id=%s AND account_id=%s",
                (target, account["id"]),
            )["n"],
            content_hash=sha(
                {"export": ex["sha256"], "account": str(account["id"]), "title": title, "caption": caption}
            ),
            status="approved",
            approved_by=actor,
            approved_at=now(),
        )
        return package
    if action in ("publish.mock", "publish.live"):
        if action == "publish.live":
            raise PolicyError(
                "PUBLISHING_DISABLED", "Live publishing is disabled. This build has no live write adapter.", 403
            )
        package = one(c, "SELECT * FROM platform_packages WHERE id=%s FOR UPDATE", (target,))
        require(package and package["status"] == "approved", "PACKAGE_INVALID", "An approved exact package is required")
        account = one(c, "SELECT * FROM social_accounts WHERE id=%s", (package["account_id"],))
        require(
            account["external_account_id"].startswith("scos-mock-"),
            "PUBLISHING_DISABLED",
            "Only isolated mock accounts are supported",
            403,
        )
        require(
            p.get("external_account_id") == account["external_account_id"],
            "PACKAGE_INVALID",
            "Exact external account ID confirmation required",
        )
        export_ready(c, package["export_id"], platform=account["platform"])
        existing = one(
            c,
            "SELECT * FROM publication_attempts WHERE export_id=%s AND account_id=%s AND state NOT IN ('rejected','cancelled')",
            (package["export_id"], package["account_id"]),
        )
        require(
            not existing,
            "PUBLICATION_UNCONFIRMED",
            "This export already has an active or confirmed attempt. Reconcile it; do not submit again.",
        )
        scheduled = p.get("scheduled_at")
        attempt = insert(
            c,
            "publication_attempts",
            package_id=target,
            account_id=package["account_id"],
            export_id=package["export_id"],
            dedupe_key=sha({"export": str(package["export_id"]), "account": str(package["account_id"])}),
            state="scheduled",
            not_before=scheduled or now(),
            provider_status={"mode": "mock", "simulate_response_lost": bool(p.get("simulate_response_lost"))},
        )
        insert(
            c,
            "jobs",
            kind="mock_publish",
            aggregate_kind="publication_attempt",
            aggregate_id=attempt["id"],
            input_hash=sha(str(attempt["id"])),
            payload={"attempt_id": str(attempt["id"])},
            max_attempts=1,
            available_at=scheduled or now(),
        )
        event(c, "publication.scheduled", attempt["id"], account_id=str(account["id"]))
        return attempt
    if action == "publish.reconcile":
        attempt = one(c, "SELECT * FROM publication_attempts WHERE id=%s FOR UPDATE", (target,))
        require(
            attempt and attempt["state"] == "unknown",
            "PUBLICATION_UNCONFIRMED",
            "Only unknown attempts need reconciliation",
        )
        receipt = one(c, "SELECT * FROM mock_provider_receipts WHERE intent_id=%s", (target,))
        require(
            receipt and receipt["account_id"] == attempt["account_id"],
            "PUBLICATION_UNCONFIRMED",
            "No verified receipt. Hold for manual investigation.",
        )
        export_ready(c, attempt["export_id"])
        c.execute(
            "UPDATE publication_attempts SET state='confirmed',external_post_id=%s,confirmed_at=now(),last_checked_at=now() WHERE id=%s",
            (receipt["external_post_id"], target),
        )
        insert(
            c,
            "publication_events",
            attempt_id=target,
            kind="reconciled",
            sanitized_response={"mode": "mock", "submit_count": receipt["submit_count"]},
        )
        return {
            "state": "confirmed",
            "external_post_id": receipt["external_post_id"],
            "submit_count": receipt["submit_count"],
        }
    if action == "analytics.fixture":
        accounts = all_rows(c, "SELECT * FROM social_accounts ORDER BY platform")
        count = 0
        for account in accounts:
            for metric, value in [
                ("views", 1840 if account["platform"] == "youtube" else 920),
                ("average_view_duration", None),
                ("shares", 28),
            ]:
                digest = sha({"account": str(account["id"]), "metric": metric, "fixture": "v1"})
                if one(c, "SELECT id FROM analytics_observations WHERE source_row_hash=%s", (digest,)):
                    continue
                insert(
                    c,
                    "analytics_observations",
                    account_id=account["id"],
                    platform=account["platform"],
                    metric=metric,
                    value=value,
                    unit="count" if metric != "average_view_duration" else "seconds",
                    dimension={"format": "short_9_16", "window_hours": 48, "synthetic": True, "sample_size": 1},
                    period_start=now() - timedelta(hours=48),
                    period_end=now(),
                    observed_at=now(),
                    source="synthetic_fixture",
                    source_row_hash=digest,
                    confidence="unknown" if value is None else "observed",
                    missing_reason="Not supplied by the synthetic fixture" if value is None else None,
                )
                count += 1
        return {"imported": count, "provenance": "synthetic_fixture", "real_channel_data": False}
    if action == "community.fixture":
        account = one(c, "SELECT * FROM social_accounts WHERE platform='youtube' LIMIT 1")
        for i, (category, text) in enumerate(
            [
                ("question", "What does the final light represent?"),
                ("suggestion", "Could you compare the opening and closing shots?"),
                ("correction", "Please make the fictional story label more visible."),
            ]
        ):
            if one(c, "SELECT id FROM comment_threads WHERE external_thread_id=%s", ("scos-fixture-" + str(i),)):
                continue
            thread = insert(
                c,
                "comment_threads",
                account_id=account["id"],
                external_thread_id="scos-fixture-" + str(i),
                topic="The Last Lighthouse",
                category=category,
                summary=text,
                anonymized_author_ref=f"fixture-viewer-{i + 1}",
            )
            insert(
                c,
                "comment_messages",
                thread_id=thread["id"],
                external_comment_id=f"scos-comment-{i}",
                redacted_text=text,
                posted_at=now(),
            )
        return {"status": "imported", "synthetic": True}
    if action == "reply.save":
        thread = one(c, "SELECT * FROM comment_threads WHERE id=%s", (target,))
        require(thread, "NOT_FOUND", "Comment thread not found", 404)
        text = p.get("text", "").strip()
        require(3 <= len(text) <= 1000, "INVALID_INPUT", "Reply must be between 3 and 1000 characters", 422)
        parent = one(c, "SELECT external_comment_id FROM comment_messages WHERE thread_id=%s LIMIT 1", (target,))
        return insert(
            c,
            "reply_drafts",
            thread_id=target,
            parent_comment_id=parent["external_comment_id"],
            draft_text=text,
            draft_hash=sha(text.encode()),
        )
    if action == "reply.approve":
        reply = one(c, "SELECT * FROM reply_drafts WHERE id=%s FOR UPDATE", (target,))
        require(
            reply and reply["draft_hash"] == p.get("expected_hash"), "CONFLICT_REVISION", "Exact reply hash required"
        )
        return one(
            c,
            "UPDATE reply_drafts SET state='approved',approved_by=%s,approved_at=now() WHERE id=%s RETURNING *",
            (actor, target),
        )
    if action == "reply.send_mock":
        reply = one(c, "SELECT * FROM reply_drafts WHERE id=%s FOR UPDATE", (target,))
        require(reply, "NOT_FOUND", "Reply not found", 404)
        if reply["state"] == "confirmed":
            return reply
        require(
            reply["state"] == "approved" and reply["draft_hash"] == p.get("expected_hash"),
            "CONFLICT_REVISION",
            "Approve the exact reply text first",
        )
        return one(
            c,
            "UPDATE reply_drafts SET state='confirmed',external_reply_id=%s,sent_at=now() WHERE id=%s RETURNING *",
            ("scos-mock-reply-" + str(target), target),
        )
    if action == "comment.delete":
        c.execute(
            "UPDATE comment_messages SET redacted_text=NULL,encrypted_raw_text=NULL,status='deleted' WHERE thread_id=%s",
            (target,),
        )
        c.execute(
            "UPDATE comment_threads SET summary='Removed by owner',status='deleted',anonymized_author_ref=NULL WHERE id=%s",
            (target,),
        )
        c.execute("UPDATE reply_drafts SET draft_text='[removed]',state='rejected' WHERE thread_id=%s", (target,))
        return {"status": "deleted"}
    if action == "experiment.create":
        require(len(p.get("hypothesis", "")) >= 10, "INVALID_INPUT", "Write a concrete hypothesis", 422)
        return insert(
            c,
            "experiments",
            name=p.get("name", "Opening shot experiment"),
            hypothesis=p["hypothesis"],
            primary_metric="average_view_duration",
            success_criterion=p.get("success_criterion", "Improve first 48-hour average view duration by 10%"),
            cohort_rules={"platform": "youtube", "format": "short_9_16", "window_hours": 48, "minimum_sample": 20},
            protocol_version="scos-experiment-v1",
            confidence_note="Inconclusive until mature comparable observations are available",
        )
    if action == "budget.reserve":
        policy = one(c, "SELECT * FROM budget_policies WHERE policy_key=%s FOR UPDATE", (NAMESPACE + "-daily",))
        amount = Decimal(str(p.get("amount", 0)))
        require(amount.is_finite() and amount > 0, "INVALID_INPUT", "Positive finite amount required", 422)
        require(
            policy["enabled"]
            and policy["consumed_amount"] + policy["reserved_amount"] + amount <= policy["limit_amount"],
            "BUDGET_EXCEEDED",
            "Paid operations are blocked by the zero-dollar local budget",
            429,
        )
        c.execute("UPDATE budget_policies SET reserved_amount=reserved_amount+%s WHERE id=%s", (amount, policy["id"]))
        return insert(c, "cost_reservations", policy_id=policy["id"], amount_reserved=amount)
    raise PolicyError("CAPABILITY_UNAVAILABLE", "This action is not implemented in the local build", 422)


def execute(c, action, target, payload, actor, key):
    require(key and 8 <= len(key) <= 150, "INVALID_INPUT", "Idempotency-Key header required (8–150 characters)", 422)
    route = f"{action}:{target or 'root'}:{actor}"
    # Transaction-scoped advisory lock serializes duplicate commands before any state change.
    c.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s,0))", (route + key,))
    digest = sha(payload)
    previous = one(c, "SELECT * FROM idempotency_records WHERE route=%s AND idempotency_key=%s", (route, key))
    if previous:
        require(
            previous["request_sha256"] == digest,
            "IDEMPOTENCY_CONFLICT",
            "Key was already used with a different request body",
        )
        return previous["response_body"]
    result = command(c, action, target, payload, actor)
    from .db import clean

    result = clean(result)
    insert(
        c,
        "idempotency_records",
        actor_id=actor,
        route=route,
        idempotency_key=key,
        request_sha256=digest,
        response_status=200,
        response_body=result,
    )
    audit(
        c,
        action,
        target or result.get("id", "local"),
        actor,
        reason=payload.get("review_note") or payload.get("reason"),
    )
    return result
