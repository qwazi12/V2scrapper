# 10 — COMPLETE GREENFIELD IMPLEMENTATION BACKLOG

All tasks target **NEW REPOSITORY `screen-central-os` ONLY**. No refactor/migration of Scrapper. Dependencies and exit tests are mandatory. Backlog tickets are independently reviewable PRs; agents may parallelize only after contracts/data boundaries are stable. **Do not skip tests to meet a schedule.** Timeline depends on people, provider approvals, technical limitations and actual QA results; the order below is a dependency order, not a guaranteed time estimate.

## Milestone map

| Milestone | Deliverable | Requires | Exit gate |
|---|---|---|---|
| M0 | Independent greenfield repo + local mock stack | Owner authorizes new repo | Boot with Scrapper offline, no credentials |
| M1 | Postgres schema, API contracts, sessions, durable workers and storage | M0 | Fault-tolerant synthetic jobs + security tests |
| M2 | Research evidence, entity resolution, claim/script gates | M1 | Fake Dune-style claim blocked; valid package approved |
| M3 | Rights-aware asset ingest, source metadata monitors, archive manifests | M1–M2 | No unauthorized file; safe ingest and independent storage |
| M4 | Creative system: formats, scripts, timelines, media renderers | M2–M3 | Real playable long/vertical/carousel outputs |
| M5 | QA/review, immutable exports, approvals and cost control | M4 | All QA gates and invalidation tests pass |
| M6 | Private platform account linking and safe mocked publish | M1, M5 | Crash-safe per-account mock publishing and receipt journal |
| M7 | Authorized analytics, trend/vidIQ adapter, audience diagnostics | M1, M6 | Provenance-tagged metrics and honest missing-data handling |
| M8 | Comments, replies, experiments, learning | M6–M7 | Draft-to-approved reply; experiment with observed data |
| M9 | Production ops, backup, cost, end-to-end and first authorized connectors | all | `make test-all`, restore drill, owner preview |
| M10 | Iterative autonomous editorial assistance, controlled autopilot | M9 + observed quality | Conservative automated drafts with no unsafe publications |

**Release strategy:** deliver a full **mocked vertical slice** as soon as M2/M3/M4 are ready; don't wait for every analytics feature. Then turn on real external read-only connectors individually; external writes last.

## M0 — NEW PROJECT BOOTSTRAP (not Scrapper)

- `SCOS-001`: Create `qwazi12/screen-central-os` with new default branch, protected main and README stating no code/data/secret sharing with Scrapper. **AC:** `git remote -v` points only to new repo; `~/dev/scrapper` untouched.
- `SCOS-002`: New monorepo structure per 02; Python/Node pinned tools, `Makefile`, `uv`/pnpm locks. **AC:** clean `make install`/`make lint` runs offline fixtures.
- `SCOS-003`: Docker Compose Postgres, S3 emulator, local fake OIDC; isolated DB `scos_local`. **AC:** no cloud account key needed to boot UI.
- `SCOS-004`: Web shell: ten workspace routes, nav, status/errors, accessible layout. **AC:** all routes navigable keyboard/mobile and real data fetch stubs.
- `SCOS-005`: GitHub Actions lint/unit/build/schema checks, protected integration evidence. **AC:** intentional failing test prevents PR merge.
- `SCOS-006`: Separate SCOS env vars, runtime isolation audit, distinct secrets namespace. **AC:** passing old Scrapper DB URL/Drive ID fails startup.
- `SCOS-007`: Separate project threat model and dependency/third-party license inventory. **AC:** verified credentials and source-use policies documented before connector coding.

## M1 — DATA AND WORKER FOUNDATION

- `SCOS-010`: Implement 43-table initial schema through reviewed Alembic migration, indexes and typed repositories. **AC:** clean PG migration and constraints test; no Scrapper migration code.
- `SCOS-011`: OpenAPI 3.1, generated TS client, `error.code`, cursor pagination and optimistic revisions. **AC:** spec/runtime drift fails CI.
- `SCOS-012`: Owner SSO and server-side session, cookie, CSRF, Origin allowlist, action audit, revocation. **AC:** auth/CSRF negative tests pass.
- `SCOS-013`: S3 object adapter with per-object presigned upload/view, SHA-256 commit and quarantine. **AC:** size/hash/path/URL-scope tests.
- `SCOS-014`: Durable SQL job queue, leases, fencing, heartbeat, cancellation and dead letters. **AC:** 3 concurrent workers and kill/recovery tests pass.
- `SCOS-015`: Transactional outbox/inbox, idempotency-key table and stable event schema. **AC:** duplicate delivery doesn't duplicate transition.
- `SCOS-016`: Cost policy/reservation ledger and provider call wrappers. **AC:** simultaneous reservations cannot exceed cap.
- `SCOS-017`: SSE job status and error UX; typed errors. **AC:** browser shows progress and blockers after refresh.

## M2 — RESEARCH AND EDITORIAL TRUTH

- `SCOS-020`: Typed provider fetcher with HTTPS/SSRF/redirect/size/content policy. **AC:** malicious URL and prompt-injection fixtures cannot invoke tools.
- `SCOS-021`: Source evidence records and actual locator capture, trust-class, date and permitted excerpt storage. **AC:** source provenance replayable.
- `SCOS-022`: Canonical movies, TV, cast/credits, release regions and source-material writers. **AC:** entity ambiguities/false cast tests pass.
- `SCOS-023`: Atomic claim store, support/contradiction semantics, freshness, reviewer actions. **AC:** fake reliable domain does not support unrelated claim.
- `SCOS-024`: Evidence adjudicator and `ResearchPackage` version hashing + owner review. **AC:** changing source revokes dependent approvals.
- `SCOS-025`: Opportunity research and source-grounded briefs; no AI-authored numerical truth. **AC:** absent demand marked unknown.
- `SCOS-026`: Script sentence claim-reference gate and independent contradiction checks. **AC:** missing verdict/role mismatch blocks output.
- `SCOS-027`: Research Desk UI with claim/evidence diffs, inline correction and conflict resolution. **AC:** actual Playwright research flow.
- `SCOS-028`: Dune-style cast/credit mistake fixture plus standard adversarial regression corpus. **AC:** every known bug fails before fix and passes afterward.

## M3 — ASSET RIGHTS AND CATALOG

- `SCOS-030`: Upload owner/authorized assets, MIME/hash/quarantine/probe and per-object access. **AC:** malformed file and traversal rejected.
- `SCOS-031`: Rights records: scope/platform/territory/derivative/expiry/proof/attribution; human adjudication. **AC:** unknown rights never `publish_eligible`.
- `SCOS-032`: Metadata-only reference source monitors and canonical channel/video IDs subject to policy. **AC:** paginated 100-item fake channel inventory dedupes; no video downloads.
- `SCOS-033`: Authorized Drive import of explicitly selected owner-held files, independent from any posting schedule. **AC:** no queue entries generated by ingest.
- `SCOS-034`: Audio/transcript/scene indexing of approved media, perceptual duplicate detection and search. **AC:** known scene retrieved with provenance; uncertain identity labeled.
- `SCOS-035`: Asset Library UI and source rights provenance pane; selection by scene/script. **AC:** no restricted asset selectable into production-ready output.
- `SCOS-036`: R2 immutable object inventory, orphan scanner, cost-aware cleanup retention. **AC:** metadata and objects reconcile with hashes.

## M4 — CREATIVE WORKSPACE AND MEDIA PRODUCTION

- `SCOS-040`: Brand kit version contract, neutral placeholders and owner brand approval. **AC:** approved font/layout/voice versions reproducible.
- `SCOS-041`: Campaign brief and independent format-specific variants, revisioned scripts/versions. **AC:** copying long script into Short is not forced.
- `SCOS-042`: Research-linked editorial scriptwriter and critique prompts. **AC:** script gate works after model failure and edit.
- `SCOS-043`: Storyboard/timeline schema, clip suggestions with asset eligibility, music/voice/captions. **AC:** invalid in/out/time/gap rejected.
- `SCOS-044`: FFmpeg/Remotion render worker for long 16:9 with chapters and thumbnail. **AC:** real decodable 1080p video from synthetic assets.
- `SCOS-045`: Native Short/Reel 9:16 template, safe-zone captions and original visual motion. **AC:** real vertical video passes probe, phone preview.
- `SCOS-046`: Carousel/image rendering (4:5 and 1:1), slide text overflow and alt text. **AC:** usable multi-page export.
- `SCOS-047`: Voice/TTS adapter and audio timing alignment; music rights and ducking. **AC:** waveform and final captions align within specified tolerance.
- `SCOS-048`: Production UI with actual video preview, storyboard editing and retry per beat. **AC:** Playwright clicks generate real files and survive refresh.
- `SCOS-049`: Packaging concepts + honest title/thumbnail revisions; no AI score as guarantee. **AC:** clearly distinct editable creative directions.

## M5 — QUALITY GATES AND IMMUTABLE APPROVALS

- `SCOS-050`: ffprobe streams/metadata gate; silence, black/freeze/clip detector and output hash checks. **AC:** known bad synthetic media blocked with timestamp.
- `SCOS-051`: Caption/spelling/safe-zone QA and meaningful media-to-script matching report. **AC:** clipped captions fail.
- `SCOS-052`: Research snapshot + asset grant validation at export and scheduled publish. **AC:** rights expiration/research edit revokes output eligibility.
- `SCOS-053`: Exact export QA report, thumbnails/contact sheet/audio waveform and playable preview. **AC:** owner inspects real asset in browser.
- `SCOS-054`: Owner approve/revoke exact `export_sha256` and editable corrections. **AC:** replacing a file cannot reuse prior approval.
- `SCOS-055`: Save media/QA artifact manifests by immutable keys and link versioned lineage. **AC:** each output traces to evidence and media rights.

## M6 — PLATFORM ACCOUNT AND PUBLISHING SYSTEM

- `SCOS-060`: OAuth link wizard with brand-new Google and Meta credentials, owner external-ID confirmation. **AC:** staging never has production publish credentials.
- `SCOS-061`: Capability matrix probes and expiry/reconnect handling for YouTube/IG/Facebook. **AC:** unsupported/expired account blocked in UI and worker.
- `SCOS-062`: Platform package creator with account-specific captions, tags, thumbnails, alt text, privacy and schedule checks. **AC:** over-limit caption blocked before provider.
- `SCOS-063`: Journal of durable per-platform attempts, idempotent owner actions, unknown-state reconciliation. **AC:** force-crash-after-provider-accept causes zero duplicates.
- `SCOS-064`: YouTube resumable upload adapter with owned test credentials and processing confirm. **AC:** mock tests pass; real test requires separate owner approval.
- `SCOS-065`: Instagram professional multi-step Reel/image/carousel connector. **AC:** mock container status vs actual publish confirmed separately.
- `SCOS-066`: Facebook Page reels/feed adapter with phased upload and receipt. **AC:** FB partial success cannot duplicate IG/YT.
- `SCOS-067`: Distribution calendar, exact account targets, pause/kill switch, complete publish report. **AC:** UI and worker both enforce production guards.
- `SCOS-068`: Drive approved-export archive with persistent resumable intents, verify, nonduplicating retry. **AC:** lost response reconciles before new create.

## M7 — DEMAND, CHANNEL ANALYTICS AND INTELLIGENCE

- `SCOS-070`: Authenticated YouTube channel Analytics importer; exact metric/dimension validation and source timestamps. **AC:** own data mapped to correct account/video.
- `SCOS-071`: Instagram/Facebook scoped Insights importer with delayed/missing-data logic. **AC:** null ≠ zero; permission missing documented.
- `SCOS-072`: Optional vidIQ adapter via officially supported separate access, OR CSV import fallback. **AC:** no dependence on Scrapper or ChatGPT tokens.
- `SCOS-073`: Opportunity score with measured/estimated/missing provenance and explicit counterevidence. **AC:** made-up search volume rejected.
- `SCOS-074`: Performance diagnostics by platform/format and comparable publication-age cohorts. **AC:** older and newer videos not compared by lifetime totals.
- `SCOS-075`: Analytics dashboard, filter-by-series, late data, retention and confidence explanations. **AC:** mock 48h/7d split accurate and available data transparent.

## M8 — COMMUNITY AND LEARNING

- `SCOS-080`: Own account comment ingestion, privacy minimization and deidentification, thread mapping. **AC:** no foreign comments claimed as owner account.
- `SCOS-081`: Comment categories, verified correction escalation to Research Desk. **AC:** meaningful correction creates review item, not auto-argument.
- `SCOS-082`: Reply drafting and exact-text approval before provider send, per-platform idempotency. **AC:** duplicate click results in one send.
- `SCOS-083`: Community UI with sorted attention/reply states and feedback-to-idea action. **AC:** user can edit/cancel and audit actions.
- `SCOS-084`: Pre-registered experiments, alternative explanations, missing/small sample handling. **AC:** tiny sample results `inconclusive`.
- `SCOS-085`: Audience learning recommendations with observation IDs, cohort definitions and next test/kill criterion. **AC:** visible reasoning and human approval of strategy updates.

## M9 — PRODUCTION READINESS AND HARDENING

- `SCOS-090`: Full `AT-001..060` suite, coverage report, real media E2E through browser. **AC:** no outstanding P0 defects or falsely green mock.
- `SCOS-091`: Source/platform provider contract test and failure matrix. **AC:** 401/403/429/5xx/timeout handled safely.
- `SCOS-092`: Rate limits, quota metering, dynamic provider capability/version config. **AC:** provider 429 honors retry-after and budget.
- `SCOS-093`: Security reviews: SSRF, CSRF, path traversal, object access, XSS, OAuth, tokens, backup. **AC:** security suite and artifact scan pass.
- `SCOS-094`: Separate staging/prod IaC + least-privileged policies + secrets lifecycle. **AC:** old Scrapper environment unaffected.
- `SCOS-095`: Disaster recovery and restore drill, monitoring/alerts, incident runbooks. **AC:** RPO/RTO measured; pending publish journal reconciles.
- `SCOS-096`: Human inspection of final content/brand quality and rights for one campaign. **AC:** owner signs off exact files, not just job metrics.
- `SCOS-097`: Owner-authorized production read integration; one controlled private/unlisted test post on exact account only if separately approved. **AC:** independent external receipt and no unintended accounts.
- `SCOS-098`: Launch switch + rollback procedure + postlaunch monitoring. **AC:** deliberate activation, no automatic cutover from Scrapper.

## M10 — CONTROLLED AUTONOMOUS EDITORIAL OPERATIONS

- `SCOS-100`: Scheduled opportunity refresh, bounded research costs, duplicate topic prevention. **AC:** no auto-publish, alerts/overrides available.
- `SCOS-101`: Approved-topic → independently researched draft → native render in a **private review queue**, with quality hold on any failure. **AC:** unattended synthetic run leaves valid review-ready artifact and blocks invalid one.
- `SCOS-102`: Rules-based production prioritization using measurable channel fit and novelty; owner adjustable. **AC:** algorithm shows WHY each item picked and uncertainty.
- `SCOS-103`: Conditional community feedback → idea recommendations, no automatic mass replies. **AC:** comments lead to drafts only.
- `SCOS-104`: Limited allowlisted auto-publishing mode considered **only after** consistent end-to-end content accuracy, rights, media QA, reconcile reliability and owner explicit consent. **AC:** kill switches and safe rollback tested; default remains off.

## Cross-cutting delivery requirements for EVERY PR

1. Commit in the **new** `screen-central-os` repository only. No access to Scrapper files, DB or credentials by default.
2. One coherent change with tests, migration where needed, API spec update, UI errors/loading/empty states and docs.
3. No credential, paid action or live external publish in CI or unattended tests. Provide exact environment/capability blockers.
4. `make lint`, relevant tests, `make test-contracts`, and touched E2E path pass; no masking failures by blanket mocks or skips.
5. No hardcoded production identifiers, arbitrary media filenames as paths, social account ambiguity, claim `supported` without evidence or unbounded model loops.
6. Include screenshots, media contact sheets/hashes, provider mock receipts and a written “what is still not proven” section when appropriate.
7. Before merging: branch review, security impact, migration reversibility/compensation, rollback action. Before production: separate owner approval.

## Implementation staffing/parallelism

- One engineer/agent can build M0–M2 sequentially, with independent tasks parallelized only after contract lock.
- Media engine and connector development can proceed in parallel after M1/M3 but need shared export/rights API contract and QA acceptance.
- Community and analytics work can develop against fixtures after M1, but cannot be declared production-verified before actual OAuth data grants.
- Codex can implement safe local tasks unattended; it must stop for missing permissions, new costs, live social writes or destructive migration. Do not claim future work occurs after a session ends unless an actual scheduled automation/service is configured.

## Exit status ledger (fill as project builds)

For each milestone maintain `status: not_started | in_progress | blocked | implemented_not_e2e_verified | e2e_verified`, links to PR, commit, test artifacts, acceptable exceptions and next prerequisites. The final full-product claim requires every FR satisfied or explicitly gated for an externally unsupported API with documented manual alternative.
