# 08 — SECURITY, INFRASTRUCTURE, SECRETS, BACKUPS AND OPERATIONS

## 1. Threat model

| Threat | Attack surface | Required control | Test |
|---|---|---|---|
| Account takeover | Private owner dashboard/OIDC session | Owner-only allowlist, strong external SSO/MFA, HttpOnly Secure session, session revocation | unauthenticated/expired/scoped tests |
| Token theft | OAuth grants, logs, frontend bundles | Envelope encryption with rotating KMS key; no client access; redacted logs | secret scan, JS bundle audit |
| Cross-site request forgery | State-changing web routes | SameSite cookie + exact Origin validation + CSRF token | forged Origin/test no token |
| SSRF | Research URL fetching, media import, redirects | HTTPS allowlist policy + private IP/DNS rebinding defense + redirect revalidation | IPv4/IPv6/metadata hosts |
| Arbitrary file read/write | User-controlled filenames, Drive names | Server-generated paths, basename normalization, isolated dirs, no traversal | `../`, Unicode, symlink tests |
| Untrusted media exploit | FFmpeg/preview/media parsers | Quarantine, MIME/size caps, security patching, sandbox/no network, low privileges, timeouts | malformed media corpus |
| Prompt injection | Search results, comments, documents | Data/instruction separation, tool permissions independent of model, schema validation | malicious source fixture |
| Unsupported factual narration | Model self-validation and dubious citations | Atomic claim/source support, independent deterministic checks, fail-closed gates | false Dune-style fact test |
| Copyright/reuse risk | Asset acquisition and publication | Rights grant, usage-specific license, owner review, attribution, explicit blocks | unlicensed asset publish blocked |
| Duplicate external publication | Retry/crash and provider unknown outcomes | Durable intent, unique unresolved state, read-before-retry, manual reconciliation | kill after provider acceptance |
| Bucket leakage | Object storage access | Private buckets, per-object short-lived signatures, no master media pass | backup/private object forbidden |
| Publishing to wrong account | Platform handle confusion or swapped session | Bind immutable external account ID + grant + human approval | account mismatch test |
| Budget overrun | Parallel paid research/TTS | Atomic budget reservation/settlement, provider allowlist, alerts | concurrent reservation test |
| Data exfiltration | Job logs, artifact downloads, webhooks | Principal-bound authorization, minimal storage, redaction, audit logs | download URL access checks |
| Supply-chain compromise | Dependencies, GH workflows, images | Lockfiles, vulnerability scanning, SBOM, protected branch, signed/reviewed deploy | CI policy checks |
| Credential reuse from Scrapper | Bad env setup | Distinct env/prefix, no secrets copy, path mismatch detection, denied cross project access | bootstrap isolation test |

## 2. Authentication and authorization design

- **One owner account** in v1, allowlisted OIDC subject/email, provider MFA enforced via identity provider. No anonymous signups, team invitation or self-service role changes in launch UI.
- Backend session stored as hashed bearer token (`sessions.token_hash`), cookie `__Host-scos_session` with `Secure`, `HttpOnly`, Path `/`, `SameSite=Lax` or stricter depending flow. Rotate session at login and sensitive changes; logout revokes server entry.
- All mutations require authenticated session, Origin allowlist and `X-CSRF-Token`; additional confirmation and audit note for deleting media, enabling publishing, modifying accounts, cost limits and grant permissions.
- `owner` can approve/publish/configure; `editor` later may draft but cannot enable publishing, approve rights or view encrypted grants; `viewer` read-only. Default owner-only means deny anything not explicitly assigned.
- OAuth callbacks use exact redirected URI, PKCE/state/nonce, external provider account identity confirmation; no querystring access tokens, no `localStorage` root token.
- File preview/download: validate owner session on issuing endpoint, return **single-object**, read-only signed URL valid ~5 min (configurable), no general media path access to backups or other campaigns.

## 3. Secret handling

- Production secrets in Railway/Vercel/Cloud secret manager; no `.env` committed, use `.env.example` with dummy values. Never paste live secret into Codex prompt or logs.
- OAuth refresh/access tokens encrypted with envelope key from secret manager, record key version, support rotation/re-encryption and revocation. Provider token is never passed to browser.
- New resource names and SCOS-only scopes; reject startup if runtime points at known Scrapper database/hostnames/folders. Include an explicit `SCOS_RESOURCE_NAMESPACE` expected value in deployment and guard against `scrapper` in sensitive resources.
- CI identity via GitHub OIDC where supported; no long-lived cloud keys in workflow file.
- Scan Git history for secrets (`gitleaks`/equivalent); remove debug payloads; rotate any confirmed exposed token, not just delete line.

## 4. Environment variable inventory

Only new `SCOS_` resources may be referenced. Example variable **names**, never real secrets:

```dotenv
SCOS_ENV=local
SCOS_RESOURCE_NAMESPACE=scos-local
SCOS_PUBLIC_URL=http://localhost:3000
SCOS_API_URL=http://localhost:8000
SCOS_DATABASE_URL=postgresql+psycopg://scos:localdev@localhost:5432/scos_local
SCOS_OIDC_ISSUER=https://identity.example
SCOS_OIDC_CLIENT_ID=replace-with-separate-client
SCOS_OIDC_CLIENT_SECRET=LOCAL_FAKE_NOT_REAL
SCOS_SESSION_SIGNING_KEY=LOCAL_ONLY_GENERATE_NEW
SCOS_ENVELOPE_KEY_VERSION=1
SCOS_ENVELOPE_MASTER_KEY=LOCAL_ONLY_GENERATE_NEW
SCOS_S3_ENDPOINT=http://localhost:9000
SCOS_S3_BUCKET=scos-local
SCOS_S3_ACCESS_KEY_ID=LOCAL_MOCK
SCOS_S3_SECRET_ACCESS_KEY=LOCAL_MOCK
SCOS_GOOGLE_OAUTH_CLIENT_ID=
SCOS_GOOGLE_OAUTH_CLIENT_SECRET=
SCOS_META_APP_ID=
SCOS_META_APP_SECRET=
SCOS_AI_PROVIDER=
SCOS_AI_API_KEY=
SCOS_VIDIQ_ADAPTER_MODE=disabled
SCOS_FFPROBE_PATH=ffprobe
SCOS_FFMPEG_PATH=ffmpeg
SCOS_PUBLISH_ALL_DISABLED=true
SCOS_PAID_CALLS_DISABLED=true
SCOS_DAILY_BUDGET_USD=0
SCOS_MONTHLY_BUDGET_USD=0
SCOS_MAX_UPLOAD_BYTES=1073741824
SCOS_MAX_ACTIVE_RENDER_JOBS=1
SCOS_LOG_LEVEL=INFO
SCOS_SENTRY_DSN=
SCOS_TRACE_OTLP_ENDPOINT=
```

Never put production secret material into the dev examples. Staging and production share no DB URL, bucket name, owner auth callback URL or provider token. For local `OIDC`, a development-only identity fixture is permitted when `SCOS_ENV=local`; it must be impossible to enable in staging/production.

## 5. Resource layout and minimum deployed services

- Vercel Project **screen-central-os-web**, distinct frontend domain. Next.js server only communicates with new API; browser does not need raw provider secrets.
- Railway Project **screen-central-os-api**, services `api`, `worker-cpu`, `worker-media`, `postgres` or managed Postgres; separate staging environment with own database and feature flags.
- Object storage: `scos-assets-staging`, `scos-assets-prod` (private). Separate public preview URLs generated for exact objects only.
- Google Workspace/Drive: a new archive root `Screen Central OS`, created only after owner authorizes. No inherited access to existing Scrapper folder.
- Provider app projects: distinct YouTube/Google OAuth client, Meta app. Test accounts or approved staging environments where supported.
- Initial concurrency: API 1 instance; CPU worker 1; media worker 1; publisher in CPU worker with DB leases and global kill flag. Scale only based on measured queue load. More replicas must not create duplicate schedulers.

## 6. CI/CD and release process

PR required checks:
1. Python lint/types/test, migration tests on clean Postgres and from previous SCOS migration, security checks.
2. Frontend lint/types/unit tests and production build; generated API client freshness check.
3. Renderer deterministic smoke: video from synthetic approved assets, ffprobe and audio/caption checks.
4. Playwright browser golden workflow against local web+API+PG+object emulator+mock providers.
5. Static security scans (dependency advisory, secret detector, container scan) with recorded exceptions/time limits.
6. OpenAPI/YAML and JSON schema validation plus drift check between FastAPI generated routes and `04_OPENAPI.yaml`.
7. Job crash/restart integration, publication idempotency, backup access, uploaded file path escape tests.

Staging preview on PR with publisher adapter hard-set `mock`; never inject production social credentials. CI reports screenshots/traces/video outputs and SHA IDs as artifacts with restricted retention.

Production pipeline: only versioned main branch after review; owner approval gate; DB backup snapshot/verified restore point; compatible additive migrations; deploy and run smoke; enable only previously approved flags. Rollback application release on error, with forward-only compensating migration where database rollback would lose data. Test provider availability but never make a test post without owner approval.

## 7. Backups, restore, data retention

- Postgres: managed daily snapshot + PITR if available; verify accessible restore in isolated staging once per month. RPO target 24h, RTO target 4h when staffed, subject to verified provider capabilities.
- R2 immutable exports: enable object versioning/backups or independent periodic manifest + redundant copies if risk warrants; record checksum to detect corruption. An object store alone is not a backup.
- Backups excluded from all general preview access, not on a public bucket or general signed media token; least-privileged restoration credentials.
- Google Drive archive is optional supplemental copy, not sole source of truth and not proof of publish readiness.
- Suggested retention defaults (owner-configurable/policy-checked): short-lived tmp files 24h after verified job finalization; render intermediates 7d; preview artifacts 30d; failed job diagnostic 30d; published originals retained indefinitely until owner changes policy; research metadata/snapshots 180d or source-policy TTL; raw comments no longer than 90d unless needed with consent, deidentified aggregates longer; audit logs 1y. Legal holds and required provider deletions override.
- Deleting user-provided assets triggers dependency and rights graph warning before deletion; preserve published content proof under allowed retention. Never delete Drive file merely to remove an internal queue entry.
- Disaster drill: restore DB+asset manifest into a completely new isolated namespace, run checksum verification, test owner login and one synthetic campaign, ensure NO live post actions available, compare recovered pending publication attempts.

## 8. Logging, metrics and alerts

Every action gets trace ID and structured event with `environment`, `job_id`, `campaign_id`, `export_id`, `publication_attempt_id` where relevant, and an error **code** (not raw unbounded provider response).

Monitor:
- Web: 5xx%, p95 latency, token/CSRF errors, UI unhandled exceptions.
- Jobs: queue depth/age, lease expirations, retries, dead letters, cost blocked, worker memory/disk, render time, interrupt recovery.
- Research: unsupported claims, source conflicts, freshness failures, wrong-entity detection, hallucination regression.
- Media: QA failure per check category, render artifacts checksum mismatch, thumbnail/caption errors, stale cache hits.
- Publishing: scheduled late, unknown>60m, duplicate suppression event, verified external completion, account mismatch, 401/403/429, revocation.
- Growth: data ingestion coverage, delayed metrics, formats with insufficient samples, subscriber conversion observation, user corrections.
- Finance: spend by provider, reserved/consumed vs policy, unexpectedly high per-campaign cost.
- Storage: capacity, outstanding multipart uploads, orphaned objects, backup failure, archive verification failures.

Alert routing defaults: owner dashboard + optional email, rate-limited by fingerprint. No automatic new paid provider purchases or extra credits.

## 9. Failure handling / incident runbooks

### SEV-1: unexpected external publication or credential compromise
1. Disable global publishing, revoke affected account grant/rotate key, stop publisher worker.
2. Snapshot DB/attempt ledger and sanitized audit logs; preserve exact export and provider receipt.
3. Determine confirmed posts and affected accounts with read-only API; never blindly delete content, seek owner approval.
4. Patch cause, add regression, review all queued/scheduled intents, require owner approval to re-enable.

### SEV-2: false content or rights issue published
1. Mark affected export/package `revoked`, pause related pending posts; inspect factual/rights evidence and affected derivatives.
2. Assess external publication and appropriate correction/removal with owner; preserve evidence and explain limitations.
3. Fix research/media validator, add adversarial fixture, rerun test and content review.

### SEV-2: jobs stuck, duplicate-risk uncertain receipts
1. Stop new submissions for affected account only, inspect stale leases and attempt journal.
2. Query provider by external receipt ID and account; if ambiguous, hold. Do not retry until absence verified or owner takes explicit informed action.
3. Reconcile independently for each platform, document outcome and prevent backfill storm.

### SEV-2: budget runaway
1. Disable paid calls, reserve no new work, terminate safe task loops.
2. Reconcile provider actuals, locate duplicate retry/usage counting bug, notify owner.
3. Only resume after cap and retry changes; never silently raise budget.

### SEV-2: storage corruption or DB outage
1. Freeze write-critical workflows and publication; preserve raw logs and storage manifests.
2. Restore into isolated namespace from verified backup; compare object hashes and publisher journal.
3. Cutover only after owner checks and smoke; do not replay ambiguous external writes.

## 10. Capacity and cost model (transparent, no guessed vendor subscription prices)

Monthly total = fixed hosting + PostgreSQL + object-store GB-month + request/transfer cost + AI input/output tokens + TTS duration/characters + rendering CPU/GPU + external service subscriptions + archive upload/retention + unexpected retries.

Record line-item unit pricing by provider/version/effective date; calculate per campaign via actual usage receipt. Display predicted cost as range, not guarantee. Daily/monthly policy defaults to zero until owner explicitly enters spending caps. Cost reservation fails closed when pricing unknown for optional paid task.

For sizing, evaluate sample schedule (e.g., 4 Shorts per week, 2 long-form/month, 6 static/carousel posts/month), asset sizes and rendered intermediates in staging; derive storage, transfer, CPU minutes and token usage before setting budget. UI shows current cost, reserved cost and worst-case next task.

## 11. Security acceptance

- [ ] Old Scrapper offline and database inaccessible; SCOS local golden test works.
- [ ] Old Scrapper production secrets/folder IDs rejected by resource isolation check.
- [ ] Owner-only authentication, CSRF and per-object access tests pass.
- [ ] No external publish from CI/staging, even with manipulated UI/flag/DB inputs.
- [ ] Unverified/rightless asset cannot be included in a `publish_ready` export.
- [ ] Unauthorized backup file download blocked with token scoped to unrelated media object.
- [ ] Concurrent cost reservations never exceed policy limit.
- [ ] Unknown external submission crash never causes automatic duplicate.
- [ ] Session secret, Google/Meta tokens and provider response secrets redacted across logs/artifacts.
- [ ] Backup restore from isolated namespace passes checksums and post-journal consistency.
