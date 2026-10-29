"""Enumerate every normative FR/AT/NFR; never equate a route or a mock with production proof."""

import json
import re
from pathlib import Path

root = Path(__file__).resolve().parents[1]
fr_notes = {
    1: "Independent local stack preserved; private Supabase schema, Google PKCE owner flow and Vercel/Railway staging deployed. Real Google provider setup/owner consent remains required.",
    2: "Manual ideas and excerpts only; compliant live discovery is not implemented.",
    3: "Reference metadata monitors and competitor inventory not implemented.",
    4: "Unknown demand and counterevidence are labeled; no observed opportunity-ranking engine.",
    5: "Manual source metadata, excerpts, timestamps and content hashes; no live snapshot acquisition.",
    6: "Atomic claim ledger, exact reviewed support and contradiction blockers tested locally.",
    7: "Structured-field mismatch tests exist; no live canonical cast/date/credit resolver or full Dune corpus.",
    8: "Claim review and script/image changes invalidate dependent approvals; not every source/license mutation path exists.",
    9: "Versioned scripts and independent format treatments; full brief/script diff and undo missing.",
    10: "Owned-image upload, decoding/quarantine, owner attestation and use-specific rights gates; licensed video ingest missing.",
    11: "No scene/audio/transcript search index.",
    12: "Real synthetic 1080p landscape rendering; rich long-form footage/chapters not implemented.",
    13: "Distinct portrait script and real 1080x1920 render; real Reel platform validation not implemented.",
    14: "Three original PNG carousel cards rendered; broader image/story format workflows incomplete.",
    15: "Local narration and safe-zone text; detailed word alignment, brand approval and complete caption QA missing.",
    16: "Exact immutable export hash/input approval and dependency invalidation tested locally; owner commercial editorial signoff outstanding.",
    17: "Basic title/caption/media-format validation against mock destinations; not a complete per-provider capability validator.",
    18: "Durable mock intent, unique unresolved/confirmed guards and lost-ack reconciliation; no real provider receipt test.",
    19: "Live writes permanently disabled; mock scheduling works, configurable per-account production controls not implemented.",
    20: "YouTube app OAuth, live analytics and controlled real upload require a separate client, adapter and owner consent.",
    21: "Meta Instagram professional app/OAuth and publish/insight adapter not implemented.",
    22: "Meta Facebook Page app/OAuth and publish/insight adapter not implemented.",
    23: "Drive resumable archive adapter not implemented.",
    24: "Synthetic comments, exact-text review and individually deduplicated mock replies; live comment sync absent.",
    25: "Synthetic provenance/null metrics and experiment registration; mature cohort diagnostics and real evidence-based recommendations absent.",
    26: "Gemini REST drafting, strict output validation, durable call intents, UTC daily/monthly budget reservations and usage settlement implemented with fault/concurrency tests. Current dated pricing is pinned; no real paid call until the owner's key and spending caps are configured.",
    27: "Durable leases/fencing, queue cancellation and event inbox; full running-render stop, dead-letter and fault matrix incomplete.",
    28: "Local backup/isolated restore verified; hosted PITR/retention/monitoring and disaster recovery not release-verified.",
    29: "Committed browser/media E2E now present; full AT-001..060 release suite and hosted owner workflow not yet verified.",
    30: "Original fixture rights, attestation and audit records; production license/policy inventory and commercial review outstanding.",
}
not_implemented = {3, 11, 21, 22, 23}
external = {20}
focused = {
    1: "test_root_points_to_independent_project",
    2: "test_production_and_cross_project_resources_fail_closed",
    3: "test_unauthenticated_workspace_denied; test_mutation_requires_csrf_and_correct_origin",
    5: "test_injection_source_never_changes_settings",
    7: "test_structured_actor_role_mismatch (generic fixture, not full Dune case)",
    10: "test_trusted_hostname_does_not_prove_claim",
    11: "test_missing_citation_blocks_script; test_correct_citation_cannot_authorize_different_sentence",
    12: "test_script_revision_revokes_approvals (script path; claim edit paths partial)",
    13: "test_contradiction_blocks_supported_claim",
    14: "test_stale_source_blocks_render",
    18: "test_expired_rights_block_publish",
    19: "test_owned_image_upload_quarantines_and_sanitizes_filename",
    20: "test_corrupt_image_upload_is_rejected (image only, not video)",
    21: "test_storage_detects_replaced_bytes",
    22: "scripts/verify_media.py verifies real dimensions; wrong-profile fixture not implemented",
    23: "test_selected_owner_image_is_used_in_frame; constrained safe-zone renderer (not OCR overflow detector)",
    24: "Real audio stream/loudness checks; full silence/clip corpus absent",
    26: "Real decode/hash/QA completion checks; incomplete-file fault case absent",
    27: "test_render_requests_deduplicate (sequential request case, not full concurrent render)",
    29: "test_script_revision_revokes_approvals; test_exact_export_hash_required",
    30: "test_backup_path_not_available_as_export",
    31: "test_parallel_budget_reservations_cannot_overspend",
    32: "test_budget_defaults_to_zero",
    33: "test_lost_mock_response_reconciles_without_second_submission (lost acknowledgment, not literal process kill)",
    36: "test_caption_limit_blocks_package",
    38: "test_live_publish_always_denied",
    39: "test_staging_cannot_use_development_login; hosted config policy",
    40: "test_reply_repeated_send_is_idempotent",
    43: "Separate platform panels; no automated cross-definition test",
    45: "test_unknown_metrics_remain_null",
    46: "UI is explicitly inconclusive; full experimental-analysis test absent",
    49: "scripts/backup.py --restore-drill verified local backup, not hosted DR",
    54: "test_duplicate_events_have_one_inbox_receipt",
    55: "test_stale_worker_is_fenced",
    56: "test_platform_rights_are_checked",
    57: "Exact external_account_id confirmation in mock submit; wrong-account fixture incomplete",
    60: "tests/e2e/golden.spec.ts mobile test; original in-app browser verification",
}
rows = []
for line in (root / "docs/blueprint/01_PRODUCT_REQUIREMENTS.md").read_text().splitlines():
    m = re.match(r"\| FR-(\d{3}) \| ([^|]+) \| ([^|]+) \|", line)
    if m:
        i = int(m[1])
        rows.append(
            {
                "id": "FR-" + m[1],
                "requirement": m[2].strip(),
                "priority": m[3].strip(),
                "status": "not_implemented"
                if i in not_implemented
                else "external_prerequisite_and_code_remaining"
                if i in external
                else "partially_implemented_or_verified",
                "evidence_and_gap": fr_notes[i],
            }
        )
ats = []
for line in (root / "docs/blueprint/09_TEST_STRATEGY.md").read_text().splitlines():
    m = re.match(r"\| AT-(\d{3}) \| ([^|]+) \| ([^|]+) \|", line)
    if m:
        i = int(m[1])
        ats.append(
            {
                "id": "AT-" + m[1],
                "scenario": m[2].strip(),
                "expected": m[3].strip(),
                "status": "focused_or_partial_coverage" if i in focused else "not_yet_release_verified",
                "evidence_and_gap": focused.get(
                    i, "No complete automated acceptance case; remains a release blocker where applicable."
                ),
            }
        )
nfr = []
for line in (root / "docs/blueprint/01_PRODUCT_REQUIREMENTS.md").read_text().splitlines():
    m = re.match(r"\| (NFR-\d+) \| ([^|]+) \| ([^|]+) \|", line)
    if m:
        nfr.append(
            {"id": m[1], "target": m[2].strip(), "verification": m[3].strip(), "status": "not_fully_release_verified"}
        )
assert len(rows) == 30 and len(ats) == 60 and len(nfr) == 12
report = {
    "baseline_commit": "175c5a56d9739e440b5401a2c34b46ed210588b2",
    "full_product_ready": False,
    "production_approved": False,
    "requirements": rows,
    "acceptance_cases": ats,
    "nonfunctional_targets": nfr,
    "release_blockers": [
        "Owner Google OAuth client and consent not configured",
        "Vercel team access grant pending",
        "Hosted authenticated golden workflow not verified",
        "Real AI/vidIQ/YouTube/Meta backend grants and complete adapters missing",
        "Full API schema conformance, media QA corpus, workload/load targets and full release suite incomplete",
    ],
}
p = root / "docs/architecture/BLUEPRINT_AUDIT.json"
p.write_text(json.dumps(report, indent=2))
lines = [
    "# Full greenfield blueprint audit",
    "",
    "Baseline: `175c5a5`. Every FR-001..030, AT-001..060 and NFR target is inventoried. Partial coverage is not a passing release gate. Production remains unapproved.",
    "",
    "## Functional requirements",
    "",
    "| ID | Status | Evidence and remaining work |",
    "|---|---|---|",
]
for r in rows:
    lines.append(f"| {r['id']} | {r['status']} | {r['evidence_and_gap']} |")
lines += ["", "## Acceptance catalog", "", "| ID | Coverage | Evidence and gap |", "|---|---|---|"]
for r in ats:
    lines.append(f"| {r['id']} | {r['status']} | {r['evidence_and_gap']} |")
lines += [
    "",
    "## Non-functional targets",
    "",
    "All 12 NFR targets are preserved in the JSON inventory. Performance at the specified staging load, WCAG AA, hosted RPO/RTO, complete provider quotas and full secrets/retention controls are not yet proven.",
    "",
    "## Release decision",
    "",
    "Do not approve production. OAuth setup, complete owner/browser staging flow, missing product functionality and acceptance coverage must be resolved first. Existing mock success is not proof of real integrations.",
]
(root / "docs/architecture/BLUEPRINT_AUDIT.md").write_text("\n".join(lines) + "\n")
print("Audited all 30 FRs, 60 AT cases and 12 NFRs. Full production release gate remains closed.")
