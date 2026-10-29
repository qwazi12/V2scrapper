# Full greenfield blueprint audit

Baseline: `175c5a5`. Every FR-001..030, AT-001..060 and NFR target is inventoried. Partial coverage is not a passing release gate. Production remains unapproved.

## Functional requirements

| ID | Status | Evidence and remaining work |
|---|---|---|
| FR-001 | partially_implemented_or_verified | Independent local stack preserved; private Supabase schema, Google PKCE owner flow and Vercel/Railway staging deployed. Real Google provider setup/owner consent remains required. |
| FR-002 | partially_implemented_or_verified | Manual ideas and excerpts only; compliant live discovery is not implemented. |
| FR-003 | not_implemented | Reference metadata monitors and competitor inventory not implemented. |
| FR-004 | partially_implemented_or_verified | Unknown demand and counterevidence are labeled; no observed opportunity-ranking engine. |
| FR-005 | partially_implemented_or_verified | Manual source metadata, excerpts, timestamps and content hashes; no live snapshot acquisition. |
| FR-006 | partially_implemented_or_verified | Atomic claim ledger, exact reviewed support and contradiction blockers tested locally. |
| FR-007 | partially_implemented_or_verified | Structured-field mismatch tests exist; no live canonical cast/date/credit resolver or full Dune corpus. |
| FR-008 | partially_implemented_or_verified | Claim review and script/image changes invalidate dependent approvals; not every source/license mutation path exists. |
| FR-009 | partially_implemented_or_verified | Versioned scripts and independent format treatments; full brief/script diff and undo missing. |
| FR-010 | partially_implemented_or_verified | Owned-image upload, decoding/quarantine, owner attestation and use-specific rights gates; licensed video ingest missing. |
| FR-011 | not_implemented | No scene/audio/transcript search index. |
| FR-012 | partially_implemented_or_verified | Real synthetic 1080p landscape rendering; rich long-form footage/chapters not implemented. |
| FR-013 | partially_implemented_or_verified | Distinct portrait script and real 1080x1920 render; real Reel platform validation not implemented. |
| FR-014 | partially_implemented_or_verified | Three original PNG carousel cards rendered; broader image/story format workflows incomplete. |
| FR-015 | partially_implemented_or_verified | Local narration and safe-zone text; detailed word alignment, brand approval and complete caption QA missing. |
| FR-016 | partially_implemented_or_verified | Exact immutable export hash/input approval and dependency invalidation tested locally; owner commercial editorial signoff outstanding. |
| FR-017 | partially_implemented_or_verified | Basic title/caption/media-format validation against mock destinations; not a complete per-provider capability validator. |
| FR-018 | partially_implemented_or_verified | Durable mock intent, unique unresolved/confirmed guards and lost-ack reconciliation; no real provider receipt test. |
| FR-019 | partially_implemented_or_verified | Live writes permanently disabled; mock scheduling works, configurable per-account production controls not implemented. |
| FR-020 | external_prerequisite_and_code_remaining | YouTube app OAuth, live analytics and controlled real upload require a separate client, adapter and owner consent. |
| FR-021 | not_implemented | Meta Instagram professional app/OAuth and publish/insight adapter not implemented. |
| FR-022 | not_implemented | Meta Facebook Page app/OAuth and publish/insight adapter not implemented. |
| FR-023 | not_implemented | Drive resumable archive adapter not implemented. |
| FR-024 | partially_implemented_or_verified | Synthetic comments, exact-text review and individually deduplicated mock replies; live comment sync absent. |
| FR-025 | partially_implemented_or_verified | Synthetic provenance/null metrics and experiment registration; mature cohort diagnostics and real evidence-based recommendations absent. |
| FR-026 | partially_implemented_or_verified | Gemini REST drafting, strict output validation, durable call intents, UTC daily/monthly budget reservations and usage settlement implemented with fault/concurrency tests. Current dated pricing is pinned; no real paid call until the owner's key and spending caps are configured. |
| FR-027 | partially_implemented_or_verified | Durable leases/fencing, active FFmpeg cancellation, isolated lease temporary files, bounded transient retries, dead letters and explicit safe retries tested. Full provider/process-kill fault matrix remains incomplete. |
| FR-028 | partially_implemented_or_verified | Local backup/isolated restore verified; hosted PITR/retention/monitoring and disaster recovery not release-verified. |
| FR-029 | partially_implemented_or_verified | Committed browser/media E2E now present; full AT-001..060 release suite and hosted owner workflow not yet verified. |
| FR-030 | partially_implemented_or_verified | Original fixture rights, attestation and audit records; production license/policy inventory and commercial review outstanding. |

## Acceptance catalog

| ID | Coverage | Evidence and gap |
|---|---|---|
| AT-001 | focused_or_partial_coverage | test_root_points_to_independent_project |
| AT-002 | focused_or_partial_coverage | test_production_and_cross_project_resources_fail_closed |
| AT-003 | focused_or_partial_coverage | test_unauthenticated_workspace_denied; test_mutation_requires_csrf_and_correct_origin |
| AT-004 | not_yet_release_verified | No complete automated acceptance case; remains a release blocker where applicable. |
| AT-005 | focused_or_partial_coverage | test_injection_source_never_changes_settings |
| AT-006 | not_yet_release_verified | No complete automated acceptance case; remains a release blocker where applicable. |
| AT-007 | focused_or_partial_coverage | test_structured_actor_role_mismatch (generic fixture, not full Dune case) |
| AT-008 | not_yet_release_verified | No complete automated acceptance case; remains a release blocker where applicable. |
| AT-009 | not_yet_release_verified | No complete automated acceptance case; remains a release blocker where applicable. |
| AT-010 | focused_or_partial_coverage | test_trusted_hostname_does_not_prove_claim |
| AT-011 | focused_or_partial_coverage | test_missing_citation_blocks_script; test_correct_citation_cannot_authorize_different_sentence |
| AT-012 | focused_or_partial_coverage | test_script_revision_revokes_approvals (script path; claim edit paths partial) |
| AT-013 | focused_or_partial_coverage | test_contradiction_blocks_supported_claim |
| AT-014 | focused_or_partial_coverage | test_stale_source_blocks_render |
| AT-015 | not_yet_release_verified | No complete automated acceptance case; remains a release blocker where applicable. |
| AT-016 | not_yet_release_verified | No complete automated acceptance case; remains a release blocker where applicable. |
| AT-017 | not_yet_release_verified | No complete automated acceptance case; remains a release blocker where applicable. |
| AT-018 | focused_or_partial_coverage | test_expired_rights_block_publish |
| AT-019 | focused_or_partial_coverage | test_owned_image_upload_quarantines_and_sanitizes_filename |
| AT-020 | focused_or_partial_coverage | test_corrupt_image_upload_is_rejected (image only, not video) |
| AT-021 | focused_or_partial_coverage | test_storage_detects_replaced_bytes |
| AT-022 | focused_or_partial_coverage | scripts/verify_media.py verifies real dimensions; wrong-profile fixture not implemented |
| AT-023 | focused_or_partial_coverage | test_selected_owner_image_is_used_in_frame; constrained safe-zone renderer (not OCR overflow detector) |
| AT-024 | focused_or_partial_coverage | Real audio stream/loudness checks; full silence/clip corpus absent |
| AT-025 | not_yet_release_verified | No complete automated acceptance case; remains a release blocker where applicable. |
| AT-026 | focused_or_partial_coverage | Real decode/hash/QA completion checks; incomplete-file fault case absent |
| AT-027 | focused_or_partial_coverage | test_parallel_identical_renders_have_one_logical_job; sequential deduplication test |
| AT-028 | focused_or_partial_coverage | test_owner_cancellation_stops_real_ffmpeg_and_fences_partial_output; stale/exhausted lease recovery tests. Literal SIGKILL/restart corpus remains incomplete. |
| AT-029 | focused_or_partial_coverage | test_script_revision_revokes_approvals; test_exact_export_hash_required |
| AT-030 | focused_or_partial_coverage | test_backup_path_not_available_as_export |
| AT-031 | focused_or_partial_coverage | test_parallel_budget_reservations_cannot_overspend |
| AT-032 | focused_or_partial_coverage | test_budget_defaults_to_zero |
| AT-033 | focused_or_partial_coverage | test_lost_mock_response_reconciles_without_second_submission (lost acknowledgment, not literal process kill) |
| AT-034 | not_yet_release_verified | No complete automated acceptance case; remains a release blocker where applicable. |
| AT-035 | not_yet_release_verified | No complete automated acceptance case; remains a release blocker where applicable. |
| AT-036 | focused_or_partial_coverage | test_caption_limit_blocks_package |
| AT-037 | not_yet_release_verified | No complete automated acceptance case; remains a release blocker where applicable. |
| AT-038 | focused_or_partial_coverage | test_live_publish_always_denied |
| AT-039 | focused_or_partial_coverage | test_staging_cannot_use_development_login; hosted config policy |
| AT-040 | focused_or_partial_coverage | test_reply_repeated_send_is_idempotent |
| AT-041 | not_yet_release_verified | No complete automated acceptance case; remains a release blocker where applicable. |
| AT-042 | not_yet_release_verified | No complete automated acceptance case; remains a release blocker where applicable. |
| AT-043 | focused_or_partial_coverage | Separate platform panels; no automated cross-definition test |
| AT-044 | not_yet_release_verified | No complete automated acceptance case; remains a release blocker where applicable. |
| AT-045 | focused_or_partial_coverage | test_unknown_metrics_remain_null |
| AT-046 | focused_or_partial_coverage | UI is explicitly inconclusive; full experimental-analysis test absent |
| AT-047 | not_yet_release_verified | No complete automated acceptance case; remains a release blocker where applicable. |
| AT-048 | not_yet_release_verified | No complete automated acceptance case; remains a release blocker where applicable. |
| AT-049 | focused_or_partial_coverage | scripts/backup.py --restore-drill verified local backup, not hosted DR |
| AT-050 | not_yet_release_verified | No complete automated acceptance case; remains a release blocker where applicable. |
| AT-051 | not_yet_release_verified | No complete automated acceptance case; remains a release blocker where applicable. |
| AT-052 | not_yet_release_verified | No complete automated acceptance case; remains a release blocker where applicable. |
| AT-053 | not_yet_release_verified | No complete automated acceptance case; remains a release blocker where applicable. |
| AT-054 | focused_or_partial_coverage | test_duplicate_events_have_one_inbox_receipt |
| AT-055 | focused_or_partial_coverage | test_stale_worker_is_fenced |
| AT-056 | focused_or_partial_coverage | test_platform_rights_are_checked |
| AT-057 | focused_or_partial_coverage | Exact external_account_id confirmation in mock submit; wrong-account fixture incomplete |
| AT-058 | not_yet_release_verified | No complete automated acceptance case; remains a release blocker where applicable. |
| AT-059 | not_yet_release_verified | No complete automated acceptance case; remains a release blocker where applicable. |
| AT-060 | focused_or_partial_coverage | tests/e2e/golden.spec.ts mobile test; original in-app browser verification |

## Non-functional targets

All 12 NFR targets are preserved in the JSON inventory. Performance at the specified staging load, WCAG AA, hosted RPO/RTO, complete provider quotas and full secrets/retention controls are not yet proven.

## Release decision

Do not approve production. OAuth setup, complete owner/browser staging flow, missing product functionality and acceptance coverage must be resolved first. Existing mock success is not proof of real integrations.
