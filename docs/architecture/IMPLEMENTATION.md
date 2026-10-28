# Implementation ledger

Local build authorized by the owner on 2026-10-28. The supplied documents are product specifications; their embedded Codex prompts do not independently authorize cloud operations or repository changes. The explicitly supplied remote remains qwazi12/V2scrapper. It is empty; no code was copied from any other project.

Architecture: Next.js App Router, FastAPI, PostgreSQL 16 and a durable leased worker; private MinIO objects. Original synthetic media rendered with FFmpeg and Pillow. No external AI, social accounts or cloud resources. The supplied initial SQL is retained unchanged. Subsequent changes use Alembic. Runtime API is a documented initial subset and extensions; exact full blueprint OpenAPI conformance is not yet claimed.

Milestones are tracked by actual evidence below. No milestone is complete solely because routes or a screen exist.

- M0: in progress — independent checkout, local dependencies, mock resource namespace.
- M1: in progress — normative schema, sessions, CSRF, audit, idempotency, worker leases, S3.
- M2–M8: not yet verified — implementation of the first local workflow underway.
- M9–M10: not started — hardening, full acceptance matrix, conservative automation.

Decisions: local development login exists only on loopback in SCOS_ENV=local; production startup is refused until OIDC is implemented. No live provider exists in this release. A local mock submit endpoint is separate from live publish. No cloud deployment or push is authorized by this implementation.

## Local release evidence — 2026-10-28

M0: local stack verified. PostgreSQL 16.6 container; Python 3.13; Next.js 16.4.3; API and separate durable worker; no external provider grants. Moto substitutes for unavailable MinIO registry images. Python `uv.lock` and npm `package-lock.json` pin installed dependencies.

M1: implemented local schema/auth/CSRF/idempotent commands/leases/fencing/inbox/S3. Unit/integration tests and browser sign-in pass. Full exact HTTP contract, load tests, envelope encryption/OIDC and production infra remain incomplete.

M2: exact passage support, reviewed identity, structured-field mismatch, contradiction/freshness and sentence-citation gates implemented. Manual source capture only; no live retriever/entity resolver. Fact sentences require exact approved text in this release.

M3: original fixtures and owned-image uploads with decode/size checks, quarantine, attested rights, private media and hashes. Full source monitors, scene/audio indexes and remote archive adapters not implemented.

M4–M5: actual 1920×1080 / 1080×1920 H.264/AAC clips and 1080×1350 PNG carousel rendered by a separate worker; browser portrait playback verified. Profile/decode/duration/loudness/basic safe layout checks, input and export hashes, owner test review and dependency invalidation implemented. Full NLE timeline, rich footage montage, voice alignment and automatic black/freeze/silence/caption fault detection remain incomplete. Synthetic owner-created template visuals are placeholders.

M6: exact mock destination packages, schedules, durable intent, independent mock-provider receipts, unknown hold, reconciliation and duplicate suppression implemented and tested through UI. All real providers require separate implementation and authorization.

M7–M8: provenance-labeled synthetic analytics, null values, deidentified test comments, individually approved hash-bound mock replies, pre-registered experiment form. Real analytics, statistical experiment analysis and live audience learning remain unimplemented.

M9: local tests/build and isolated backup restore pass. Production hardening, full 60-case acceptance matrix, live provider matrices and deployment remain incomplete.

M10: not implemented. No unattended editorial generation or autopublishing is enabled.

No production-ready or full-blueprint completion claim. No cloud deployments, real social writes, paid API calls, remote Git pushes or existing Scrapper changes occurred.
