# SCREEN CENTRAL OS — COMPLETE GREENFIELD BUILD PACKAGE

**Specification:** SCOS-BP-1.0 · **Date:** 2026-10-28 · **Owner:** Screen Central · **Status:** implementation specification; software has NOT been built by this package.

## The single most important constraint

**THIS IS A NEW PROJECT, NOT A REFACTOR, FORK, BRANCH, PLUGIN, OR REPLACEMENT OF `qwazi12/scrapper`.**

- NEW repository: proposed `qwazi12/screen-central-os` (create only after owner approval).
- NEW Mac checkout: `~/dev/screen-central-os`, never inside `~/dev/scrapper`.
- NEW Vercel project, Railway project/services, PostgreSQL database, object-storage buckets, Google OAuth client, Meta application, authentication secrets, service accounts and test environments.
- NEW namespaced runtime identifiers: `scos-dev`, `scos-staging`, `scos-prod`. Do not reuse Scrapper `DATA_DIR`, DB, buckets, cookies, scheduler, OAuth redirect URIs, publish-provider profile, API keys, or Google Drive folders.
- Treat the old Scrapper application as an **external reference only**. Read-only comparison is permitted when the owner permits it. Absolutely no code copy, database import, shared credentials, deployment or traffic cutover unless separately reviewed and explicitly authorized.
- The new app must launch without connecting to any real social account or sending paid API requests. Default is local synthetic data, mock providers and disabled publishing.

## What is specified here

This is a multi-file **build-ready blueprint**, not a completed implementation. All software behavior under our control is defined by contracts, states, gates and acceptance tests. Third-party grants, data availability, copyrighted footage, external budgets, and audience growth remain prerequisites/uncertainties—not guarantees.

Read in this order:

| File | Purpose / authority |
|---|---|
| `01_PRODUCT_REQUIREMENTS.md` | Goals, roles, editorial identity, screens, comprehensive functional requirements, workflows, NFRs |
| `02_ARCHITECTURE_AND_WORKFLOWS.md` | Technology decisions, runtime topology, queue/leases, orchestration, state machines, failure semantics |
| `03_DATABASE_SCHEMA.sql` | Executable initial PostgreSQL DDL, indexes, integrity constraints (subsequent migrations via Alembic) |
| `04_OPENAPI.yaml` | Machine-validatable HTTP API contract, representative detailed schemas, canonical errors, routes |
| `05_RESEARCH_AND_AI.md` | AI agent contracts, retrieval, source trust, independent claim verification, prompt design, budget controls |
| `06_MEDIA_AND_CONTENT.md` | Source ingestion, permissions, all content formats, scripts, visual planning, render pipeline and QA |
| `07_SOCIAL_ANALYTICS_AND_GROWTH.md` | Connectors, publishing/reconciliation, social engagement, metrics, experiments, learning |
| `08_SECURITY_INFRA_OPERATIONS.md` | Threat model, security, CI/CD, backups, observability, incident recovery and cost enforcement |
| `09_TEST_STRATEGY.md` | Test fixture matrix, actual browser/media testing, quality gates and acceptance evidence |
| `10_DELIVERY_BACKLOG.md` | Directed build order; explicit scoped epics, dependencies, PR sizes and release gates |
| `11_CODEX_BOOTSTRAP.md` | Ready-to-run greenfield Codex commands and a comprehensive implementation instruction |
| `12_CONTRACTS_AND_DECISIONS.md` | Object/event contracts, source inventories, open external readiness dependencies, ADRs and change control |

The `03_DATABASE_SCHEMA.sql` and `04_OPENAPI.yaml` are **normative** for the initial build; engineering may extend them through reviewed migrations/versioned API amendments but must not silently change semantics. The full detailed business workflow specifications are normative for acceptance.

## Explicitly locked product decisions

1. **Owner-only private application**; single media brand at launch, no SaaS or public marketplace.
2. **Editorial campaign** is the top-level identity; research claims and source snapshots are versioned and auditable.
3. **Audience growth, accuracy and creative value** outrank upload count. Publishing is off until manually enabled per account after production readiness.
4. **No content is automatically marked factual because an LLM or a high-reputation domain says so**. Specific claims require appropriate source support and resolution of contradiction.
5. **A rendered MP4 is not a passing video**. Production readiness requires technical QA, editorial QA, a supported rights/use basis and exact immutable export approval.
6. **No automatically copying third-party audiovisual files from YouTube**. The research catalog stores compliant metadata/links; full file ingestion is supported only for files owned by or expressly authorized for Screen Central under platform rules.
7. **At-most-one unconfirmed publication attempt per immutable export/account/platform**. Unknown provider result is a hold for reconciliation, not automatic retry.
8. **No uncontrolled auto-replies**. Draft responses and approved individual replies; never fake engagement.
9. **Only observed data may be labeled observed**. Missing metrics are `unknown`; estimates, heuristics and AI opinions are labeled.
10. **Always test using isolated local/staging data; no production account or cost effects without explicit approval.**

## End-to-end definition of a usable system

A local operator, without Scrapper installed and without real provider keys, must be able to: sign into an owner-only test account; discover or create a candidate; attach sources and adjudicate facts; create a campaign; produce original long, vertical and carousel deliverables using rights-cleared synthetic assets; inspect media with ffprobe plus human preview; approve exact hashes; schedule a mock platform publication; prove duplicate-attempt prevention after a forced crash; import simulated comments/analytics; and observe a learning recommendation with evidence. Real integrations are independently gated by their own capability tests.

## Platform policy references checked 2026-10-28

- YouTube developer policies: https://developers.google.com/youtube/terms/developer-policies
- YouTube videos.insert and uploads: https://developers.google.com/youtube/data/reference/rest/v3/videos/insert and https://developers.google.com/youtube/data/guides/uploading_a_video
- YouTube Analytics channels / metrics: https://developers.google.com/youtube/analytics/channel_reports and https://developers.google.com/youtube/analytics/metrics
- Meta official Postman collections: https://www.postman.com/meta/instagram/documentation/6yqw8pt/instagram-api and https://www.postman.com/meta/facebook/documentation/r56bjfd/facebook-api
- Drive resumable uploads: https://developers.google.com/workspace/drive/api/guides/manage-uploads
- R2 S3 API / presigned URLs: https://developers.cloudflare.com/r2/api/s3/api/ and https://developers.cloudflare.com/r2/api/s3/presigned-urls/
- YouTube channel monetization / reused content: https://support.google.com/youtube/answer/1311392

**External API availability and app permissions must be revalidated at the implementation date.** Provider API changes are handled by capability/version matrix and explicit feature flags; do not silently substitute undocumented endpoints.

## What “complete” means

This package specifies **all core components, data contracts, state transitions, permission boundaries, failure behavior, test obligations, owner actions, CI gates and delivery sequencing** for the intended product. It is not a promise that external integrations will all be granted or that any video will get views. Such dependencies are explicitly tracked. A greenfield implementation still requires actual development, OAuth registration, testing, deployment and ongoing iteration.
