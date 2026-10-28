> Staging readiness branch: the original local release has now been pushed and verified on `qwazi12/V2scrapper` and preserved as `local-working-175c5a5`. See [staging setup and current gates](docs/architecture/STAGING.md) and the [full blueprint audit](docs/architecture/BLUEPRINT_AUDIT.md). The historical local-release notes below describe the preserved baseline; they do not mean production is complete.

# Screen Central OS

Independent greenfield application; **not Scrapper**. Built locally in `~/dev/screen-central-os`. The owner-supplied `qwazi12/V2scrapper` Git remote is used. The local release is pushed and tagged; staging work is isolated on this branch. No source was copied from another project.

## Run on this Mac

Requires Python 3.13, uv, Node 24, Docker Desktop, FFmpeg/ffprobe. On macOS, local speech uses the built-in `say` command. Linux uses a clearly labeled test tone until a narration adapter is configured.

```sh
cd ~/dev/screen-central-os
make install
make dev
```

Open **http://127.0.0.1:3100** and choose **Enter local owner workspace**. This is an explicitly local development identity, available only with the default local environment. Production/staging startup is refused. API: port 8100, isolated PostgreSQL: 55432, S3 emulator: 59000. Everything binds to loopback. Ctrl+C stops a stack started by `make dev`; `make down` also stops its recorded processes and database container. Data volumes and `.runtime/` are preserved.

If a port is occupied, stop the existing SCOS app first. The launcher refuses to silently attach to an unknown service. No credentials from any other application are needed.

## Working local workflow

1. Control Room → **Create original test story**.
2. Research Desk → inspect the two source passages → review each claim → approve the research package.
3. Create the campaign. The landscape, portrait, and carousel have independent script treatments; all factual lines carry claim IDs.
4. Campaign Studio → approve each exact script → render. A separate worker claims PostgreSQL jobs with leases and fencing epochs.
5. Production → inspect the actual H.264/AAC video or PNG carousel in Quality Review. Hashes, input snapshots and technical checks are shown.
6. Record a test review note and approve the exact export. Script/research/asset changes invalidate eligibility and dependent approvals.
7. Distribution → choose the approved export and exact `scos-mock-*` destination → create the platform package → schedule mock submission.
8. With lost-acknowledgment simulation checked, the attempt is held as `unknown`. **Reconcile receipt** confirms the existing mock post without resubmission. A second active/confirmed attempt for the same export/account is rejected.
9. Community → import test comments → save one reply → approve its exact hash → send a mock reply. Analytics → import explicitly synthetic observations. Learning → register an experiment without claiming a conclusion.

For a new original story, use **New idea** and add permitted source excerpts in Research Desk. Excerpts are owner-supplied, not independently retrieved. Resolve canonical identity and review each exact passage. The initial fact checker only accepts factual script lines that exactly match approved atomic claims. Asset Library accepts owned PNG/JPEG/WebP images, quarantines them pending a specific ownership attestation, and lets you select rights-reviewed images in Campaign Studio. This is a limited graphic-based renderer, not yet a footage editing system.

## Data and safety boundaries

- The supplied initial PostgreSQL schema is applied unchanged by Alembic `scos_0001`. `scos_0002` adds the independent mock receipt journal and render deduplication index.
- `SCOS_` configuration and isolated `scos_local` / `scos_test` databases. Tests truncate **only scos_test**, never the application database.
- HttpOnly/SameSite session cookie, server-side token hash, exact Origin validation and CSRF headers for authenticated mutations; local login also checks Origin.
- Private S3 adapter plus content-addressed local object mirror. The installed MinIO image was unavailable from registries; **Moto** provides the local S3 emulator instead. Moto state is ephemeral; the verified local mirror and PostgreSQL retain local app media across restarts. This is not a production storage or backup design.
- Original fictional fixtures only; no YouTube audiovisual download, paid model call, real post, public reply, OAuth grant, cloud resource, or publishing enablement path.
- The prototype has no production OIDC, live social adapter, or cloud deployment configuration. The zero-dollar budget and live publishing gate cannot be enabled through the UI.
- Manual rights attestation is not an independent legal verification. Synthetic test approvals are not commercial editorial signoff.

## Verification

```sh
make lint
make test-backend       # 42 tests at handoff; isolated PostgreSQL + running S3 emulator
make test-contracts     # validate reference/runtime schemas; report actual coverage
make test-media         # independently hash/probe/decode existing exports
make build
make restore-drill     # backup plus recovery into a NEW scos_restore_* database
```

The test suite covers research/evidence gates, structured actor-role mismatches, source freshness, missing citations, script revisions, ownership and platform rights, export hashes, durable idempotency, concurrent budget reservations, concurrent worker claims, stale-worker fencing, event inbox deduplication, lost mock response reconciliation, exact-text reply send deduplication, null analytics, local sessions/CSRF, uploads and object-path isolation.

Browser verification was performed through the live app, including local login, unreviewed-research rejection, claims, campaign/scripts, three real renders, portrait playback, exact export approvals and mock unknown → reconciled publication. See `docs/architecture/VERIFICATION.md` for the evidence ledger. No claim is made that the entire 60-case blueprint acceptance suite has passed.

## Remaining work

This is a functioning **first local release**, not the entire production product specified in `docs/blueprint`. `docs/architecture/IMPLEMENTATION.md` and `contract-coverage.json` distinguish implemented behavior from remaining requirements. The full 89-route reference API is not implemented (27 paths present plus explicit local command extensions; exact full schema conformance remains open). Major remaining work includes production OIDC/OAuth, compliant live retrieval and structured-provider connectors, a full editable media timeline/shot index, automatic caption/audio fault detection, rich native long-form media templates, live analytics/imports, per-provider contract matrices, complete FR/AT coverage, production infrastructure and owner editorial signoff.

No hidden automation continues development after this session. The running local app worker only handles jobs explicitly queued in this local database.
