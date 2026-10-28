# 01 — PRODUCT REQUIREMENTS AND EXPERIENCE SPECIFICATION

## 1. Product charter

**Working name:** Screen Central OS (SCOS). **Role:** private production/growth operating system for the existing Screen Central entertainment media brand. **Users:** one owner and, optionally later, explicitly invited editors. Multi-tenant billing and agency features out of scope.

**North-star outcome:** more genuinely returning viewers and subscribers/followers who choose Screen Central's original entertainment coverage. Secondary outcomes: accurate content, positive engagement, consistent creative quality, lower avoidable rework, safe distribution and transparent cost.

**Success is not:** raw output count, hashtags, generic prompt scores, sensational thumbnails that don't match videos, copied third-party edits, generic auto-replies, or platform API uptime in isolation.

## 2. Brand and editorial positioning

**Audience hypothesis:** English-language viewers who enjoy film/TV moments, characters, franchise explanations and thoughtful recommendations. Do not treat this as proven demographic data. Detect and revise using owner's authenticated analytics.

**Editorial families for initial experiments** (editable; none is locked forever):

- **Moments Explained:** short original analysis of impactful scenes/characters and why they matter; respectful of spoilers, source context and media rights.
- **What We Know:** concise, accurately verified movie/TV releases, casting, sequel status and franchise news; strong disclosure of rumor/speculation.
- **Worth Watching:** justified rankings, film/series discoveries, comparisons, recommendation lists, original review arguments.

**Voice:** clear, energetic, specific, credible, fan-aware, non-hyperbolic except when supported. Never invent “official” trailers, false dates, quotes, awards, sources, or audience demand. Never claim review/watch of footage not actually analyzed.

**Initial platforms:** YouTube long-form, YouTube Shorts, Instagram professional account, Facebook Page. Third parties optional when official API/permissions allow. Target channel IDs require explicit owner linking; public handles alone do not authorize publishing.

## 3. Complete workspace map and UX acceptance

### 3.1 Control Room `/`
- Top: owner-safe state (development/staging/production), connected-account health, publish kill switch, costs, current jobs, provenance warnings.
- “Needs attention” queue: conflicting fact, rights unknown, inadequate source support, broken export, expiring grant, uncertain publication, spend limit, low-confidence metric.
- “Next opportunities”: transparent rationale, measured/estimated fields, human accept/reject controls.
- Recent campaigns, approved drafts, scheduled platform variants, recent performance, useful audience feedback.
- Action drill-down must preserve the exact underlying campaign/project/version. No decorative or nonfunctional actions.
- Default lists have search/filter/pagination, loading/error/empty states, accessible keyboard labels and confirmation of irreversible actions.

### 3.2 Discover `/discover`
- Topic cards filter by media family, channel-fit, format, release date, sentiment, sourcing evidence, novelty and production readiness.
- Compare recommendations against own-channel history and external observed signals; show provenance and time ranges.
- Competing ideas grouped to avoid redundant publishing. “Why now?”, “Why us?”, “Counterevidence?”, “Source?” and “Cost to try?” are mandatory fields.
- Operator can pin, reject (with reason), defer, refine, approve into an editorial brief; changes are audited. Discovery never queues a social upload.

### 3.3 Research Desk `/research/:id`
- Split view: facts, evidence excerpts/links, citations, contradictions, freshness, independent reviewer verdict and source retrieval timestamps.
- Atomic claim actions: support, contradict, needs-review, reject. Review requires cited matching passage/structured-provider field.
- Side-by-side cast/character/year/production credits, official page and TMDB/IMDb metadata; display provenance for each.
- Source documents are untrusted input; instructions embedded in a webpage never control system behavior.
- Owner may override with written justification; overridden facts remain visibly human-reviewed and auditable.

### 3.4 Campaign Studio `/campaigns/:id`
- Select editorial objective, viewer promise, hook, original angle, spoilers, formats, variant plans and target platform(s).
- Scripts and storyboards versioned with diff and undo. Each sentence maps to claim IDs or is marked subjective/editorial/transition.
- Explain why each format is or is not produced. No automatic content multiplication merely because a campaign exists.
- Approval gates appear inline with exact failure reasons and easy correction paths.

### 3.5 Asset Library `/assets`
- Search licensed/owned assets by name, film, person/character label (confidence), scene, mood, action, orientation, quality, usage rights and expiry.
- Ingest via owner upload, authorized Drive folder, licensed library, generated original imagery/audio, approved provider links.
- Distinguish `reference_only`, `rights_pending`, `publish_eligible`, `expired`, `restricted` and `quarantined`.
- Inspect license proof, restrictions, expiry, crop, clip timing, transcripts, audio and shot storyboard. Full third-party YouTube video downloading is not provided by default.

### 3.6 Production Studio `/production/:campaign_id`
- Native format templates: long 16:9, Shorts 9:16, Reels 9:16, story-size graphic, 1:1/4:5 image/carousel, static discussion card.
- Timeline: chapter/beat, script line, voice segment, matching approved asset, transitions, onscreen captions, music/FX, target duration and style settings.
- Actual playable preview with timestamps, warnings, selected alternative shots, rerender segment and “regenerate with feedback”.
- Render job progress via SSE/event stream; owner can cancel/retry only safe stages. Preserve previous approved exports.

### 3.7 Quality Review `/review`
- Preview and scrub final exports, waveform, contact sheet, captions, technical diagnostics, unsupported claims, rights exceptions, brand/editorial checklist.
- “Approve export” records exact SHA-256 of immutable file, claims/rights snapshot hash, source/campaign version, actor/time and target formats.
- Any change to script, evidence, asset, license, output or package invalidates downstream approval. Reapprove after reinspection.
- Separate editorial approval from technical pass; final publication needs both plus rights and account checks.

### 3.8 Distribution `/distribution`
- Calendar per platform/account; distinct per-platform post copy, caption length checks, hashtags, thumbnails, alt text, original media variant and accessible review.
- Per-destination dry-run, schedule, pause, cancel, retry-after-reconciliation. Post records show external IDs and `unknown` statuses clearly.
- Global kill switch, per-account kill switch, no publishing by default, no invisible background job that assigns a destination.
- Staging uses mocks ONLY. Owner can explicitly activate a production connector after capability check.

### 3.9 Community `/community`
- Connected-account comments grouped into actionable questions, corrections, requests, debates, spam and positive feedback.
- AI drafts reply; owner must approve exact text and destination. No automatic public reaction, reply, follow or DM.
- Link comment to original campaign and next-idea suggestion. Preserve platform deletion/moderation state; allow privacy cleanup.

### 3.10 Analytics `/analytics`
- Source-dated observations on views, engaged views, impressions when authorized, watch time, retention, interactions, follower/subscriber changes, production cost and publication age.
- Split long-form/Shorts/Instagram/Facebook; no cross-platform addition of non-comparable view definitions.
- Compare age-normalized cohorts (e.g., first 48h, 7d) and consistent baselines. Report missing coverage and small sample warnings.
- Show hypotheses, experiments, interventions, counterevidence, actual result and confidence. No causal claims from correlations.
- Feedback informs suggestions; does NOT secretly modify approved publishing rules or model weights without recorded change.

## 4. Functional requirements (IDs are stable and testable)

| ID | Requirement | Priority / owner proof |
|---|---|---|
| FR-001 | Independent app bootstrap; owner account; separate credentials | P0; start with old project offline |
| FR-002 | Discover ideas via manual and compliant integrated sources | P1; source provenance displayed |
| FR-003 | Track competitor/channel reference metadata without downloading videos | P1; dedup by canonical external IDs |
| FR-004 | Reasoned and evidence-separated opportunity ranking | P1; missing evidence does not appear as zero |
| FR-005 | Capture source snapshots/structured fields, URL, retrieval date | P0; immutable source IDs and hashes |
| FR-006 | Atomic claims and contradictory evidence | P0; contradicting source blocks auto-approval |
| FR-007 | Independent structured identity/date/cast/credits checks | P0; seeded incorrect Dune-style case fails |
| FR-008 | Human adjudication with audit and version invalidation | P0; approval invalidated on any claim edit |
| FR-009 | Versioned editorial briefs, scripts, hook alternatives | P1; inspect diffs, undo |
| FR-010 | Rights-aware asset library and original uploads | P0; publish rejects unknown/restricted rights |
| FR-011 | Scene/caption/audio/visual indexes for approved assets | P1; indexed asset returned with proof |
| FR-012 | Long-form video render and previews | P1; playable 16:9 tested export |
| FR-013 | Independently authored Shorts/Reels | P1; playable 9:16 export, not forced crop |
| FR-014 | Original carousel/static social graphics | P1; ordered export and legibility check |
| FR-015 | Voice, captions, fonts, brand kit and style consistency | P1; captions and audio synced |
| FR-016 | Immutable export QA and human approval | P0; changed export invalidates approval |
| FR-017 | Platform packaging and per-platform validation | P1; fail invalid caption/media with details |
| FR-018 | Durable publication attempts and reconciliation | P0; crash cannot cause duplicate external post |
| FR-019 | Per-account kill switch, schedule and owner approval | P0; staging can never publish |
| FR-020 | Authorized YouTube publish and analytics | P1; account-specific OAuth and capability tests |
| FR-021 | Authorized Instagram professional publish and insights | P1; container+publish test or documented gate |
| FR-022 | Authorized Facebook Page publish and insights | P1; status confirmed or appropriately gated |
| FR-023 | Google Drive optional archive with resumable upload | P1; no orphan or wrong-folder archive |
| FR-024 | Comments triage and individually approved replies | P2; no unapproved public reply |
| FR-025 | Experiments, age-normalized metrics, learning recommendations | P2; evidence-based recommendation report |
| FR-026 | Budget reservations, provider quotas, model usage ledger | P0; parallel calls cannot overspend cap unchecked |
| FR-027 | Job leases, recovery, stop, dead-letter and audit | P0; fault-injected replay safe |
| FR-028 | Owner data export, backup restore, observability and disaster recovery | P0; restore drill passes |
| FR-029 | Local real-UI E2E suite plus video/contact sheet inspection | P0; golden workflow run evidence |
| FR-030 | Attribution, copyright/reuse decision and source auditability | P0; blocked unlicensed publication |

P0 means required for first real production use, not necessarily completed before any development; P1 means minimum full product; P2 means deeper growth suite. All FRs must be implemented to claim complete product delivery.

## 5. Detailed story workflows

### S1. News investigation
`signal → identity + date resolution → reliable primary/independent sourcing → claim ledger → rumor labels → angle → fact review → script → render → QA → approve → platform packages → publish → metrics`.
- Any unconfirmed date/title treated as unknown or explicitly reported rumor.
- Corrections after publication create a new revision + incident; optional clarification and corrected new export, never silently mutate record.

### S2. Ranked countdown
`propose a premise → define inclusion/exclusion rubric → discover 5/10/15 eligible works → canonical identity resolution → evidence for placement → editorial order and hook → verify statistics → per-entry storyboard → render segments + join → QA and rights → publish`.
- If fewer than N eligible items, propose lower N for owner review; never pad with fabricated items.
- `why_it_ranks` cannot be empty for an approved item. Statistical ranking requires actual measured and cited data; subjective rankings labeled editorial.

### S3. Moments Explained (short-form)
`viewer problem/emotion → original claim/interpretation → contextual evidence → approved source visuals or original assets → 1-sentence hook → premise → analysis → payoff → deliberate cut and caption design → QA → platform-specific render → publish`.
- A recognizable film clip without substantial original analysis is not automatically approved.

### S4. Carousel / still / poll
`editorial brief → selected format → 3–10 slide outline (configurable) → per-slide supporting claims → portrait legibility/safe-zone check → source attribution and rights → social package and approval`.
- Polls are published through native platform APIs only where supported/authorized; otherwise export manual posting pack. Never automate community-platform features that APIs do not expose.

### S5. Community-led follow-up
`fetch authorized comments → deidentify and classify → identify recurrent need → propose editorial opportunity → review with sources → produce original content → optional individually approved reply linking new content if relevant`.

### S6. Media ingest and archive
`authorized upload/source → source rights proof → file integrity and MIME/size validation → quarantine scan → content hash and canonical identity → archive object → metadata/transcript/scene analysis → searchable catalog → approved project use → Drive export`.

### S7. Performance-led revision
`published post and exact export → observed metrics with capture date → age-normalized comparison → uncertainty assessment → next test hypothesis → experimental proposal → owner acceptance`.
- Platform metrics are not substituted when missing; don't declare thumbnail cause without experiment.

## 6. Non-functional requirements / service targets

| ID | Target | Acceptance method |
|---|---|---|
| NFR-01 | Local boot `make dev` with mock providers and a usable test login within 2 minutes on documented dev hardware (excluding first install) | cold-ish local smoke |
| NFR-02 | API read p95 < 500 ms for indexed list/detail operations at 50k rows in staging, excluding external calls | load test |
| NFR-03 | UI usable at 375px and desktop 1280px, WCAG 2.2 AA target for key flows, keyboard/screen reader labels | Playwright axe and manual |
| NFR-04 | No production write without explicit owner approval and exact destination | privilege/unit/E2E tests |
| NFR-05 | At most one unresolved submission attempt per (export hash, account, platform) | concurrency/fault tests |
| NFR-06 | No approved export mutates in place; prior versions retained per policy | hash and approval tests |
| NFR-07 | Backups: PostgreSQL PITR where supported; documented RPO <=24h, RTO <=4h during business hours after restore drills (initial targets, not promises) | staging restore drill |
| NFR-08 | Job recovery after process termination; no unbounded external retry or write | kill/restart test |
| NFR-09 | Per-provider daily/monthly cost caps and reservations; unknown pricing blocks optional paid step | parallel cost tests |
| NFR-10 | Explicit policy/data retention/deletion controls | compliance tests |
| NFR-11 | 95% of background-job state transitions reflected in UI within 10s under normal operation | SSE integration test |
| NFR-12 | No sensitive provider tokens, raw logs, or source credentials exposed in UI or downloadable job artifacts | scanning and authorization tests |

Availability of external services and extraordinary render sizes cannot be guaranteed. Monitor targets with actual tests before claims.

## 7. Release-level criteria

- **Local Alpha:** all P0 identity, data, research, rights, jobs, export validation and mock publishing tests pass. Complete synthetic golden campaign from browser.
- **Private Beta:** original long, short and carousel outputs can be reviewed and approved. Platform read-only connectors work or show explicit gate; approved staging content never crosses production boundary.
- **Production v1:** owner-only authorized platform connectors pass exact-account tests, publish journal reconciles, backup restore drill recorded, cost alerts and kill switch tested, reporting available with honest gaps.
- **Full Product v1:** all FR-001..030 satisfied or an external platform-specific capability explicitly disabled because not granted; every disabled capability has UI explanation and a supported manual workflow. No features silently pretended.
