# Isolated staging readiness

The original working local release is preserved on GitHub `main` at `175c5a56d9739e440b5401a2c34b46ed210588b2`, tagged `local-working-175c5a5`. Its Mac checkout and running database remain separate from this `staging-readiness` worktree. A Git bundle and fresh local database/media backup were saved before changes.

## Implemented in this branch

- Owner-only Google OIDC authorization-code flow with PKCE, nonce, signature/issuer/audience/expiry/email verification, single-use browser-bound login state, stable subject binding and Secure HttpOnly `__Host-` session cookie in hosted environments.
- Local fixture login is forbidden in staging/production. No anonymous signup. With Google configuration missing, staging shows a locked sign-in page; production refuses startup entirely.
- Additive Alembic migration `scos_0003` creates transient OIDC state. Migration startup is serialized by a PostgreSQL advisory lock.
- Hosted environment validation requires an isolated SCOS database and bucket, HTTPS frontend/storage, and separate credentials. Social publishing and paid calls remain disabled.
- Durable private S3 is authoritative in hosted environments; no local mirror dependency. Content-addressed keys, conditional immutable writes and SHA-256 validation remain enforced.
- Non-root Docker image with FFmpeg, DejaVu and local `espeak-ng` speech synthesis. Narration duration sets scene duration to avoid silently cutting off a sentence.
- Configurable server-side frontend API origin; environment-aware owner login and labels.
- All 30 FRs, 60 acceptance scenarios and 12 nonfunctional targets inventoried in `BLUEPRINT_AUDIT.md/json`. Full production approval remains blocked.
- Secret-free GitHub CI; real Playwright golden workflow and mobile keyboard/layout checks against an isolated database, plus focused identity/storage tests.

## Created resources (only staging)

- Railway project: `screen-central-os-staging` / `e2e191c0-c5b9-4d13-8be3-c39bb3acbf58`
- Railway environment: `staging` / `b6c0ad33-cfd6-4d5a-8026-1b242b3c036e`
- PostgreSQL: `scos-postgres`, database `scos_staging`, dedicated persistent volume.
- Private S3 bucket: `scos-staging-media` in `iad`. Credentials are Railway reference variables, never copied into source.
- API: `scos-api`; worker: `scos-media-worker`. Separate memory/CPU limits. Worker has no public domain.
- Frontend: `scos-web` on Railway, `https://scos-web-staging.up.railway.app`. Its server proxies the API through the same origin. This provides staging while Vercel team consent is pending.
- Vercel project: `screen-central-os-staging` / `prj_HiGZPPkEqxaNVUOQaTmgMY65nQXv`. Team authorization is needed before frontend configuration/deployment.

No existing Scrapper resource is modified. No production deployment is approved.

Railway service settings explicitly select `Dockerfile` for API/worker and `Dockerfile.web` for the frontend. No deprecated `railway.json` is required. Each source is pinned to a reviewed Git commit. The frontend container uses Next's standalone output and contains no API/database/storage secrets.

### Hosted verification

PostgreSQL, API and worker deployed successfully from `52ffe7632953dc8969dfabb427078ee7c16d8ead`. Public readiness confirms the database and private bucket. Anonymous workspace access returns 401, local fixture login returns 403, and an unconfigured Google login returns 503. A synthetic 18-second narrated portrait render inside the Railway worker passed profile, H.264, audio, full decode, duration and loudness checks and was retrieved from private S3. Editorial approval remains required. This smoke does not replace an authenticated browser-to-queue-to-media test.

GitHub Actions run `40782296015` passed the full isolated Linux test stack. The connected GitHub integration rejected draft PR creation with 403; the branch is pushed and reviewable directly.

## Required owner setup

1. Authorize the existing Vercel connection for the `qwazi12s-projects` team using the provider consent link supplied in chat.
2. Select the owner Google email and register a **new SCOS-specific** Google web OAuth client. After the Railway frontend hostname is verified, the callback is `https://scos-web-staging.up.railway.app/api/v1/auth/oidc/callback`. If staging moves to Vercel, update the API's `SCOS_PUBLIC_URL` and the Google registered callback together.
3. Set `SCOS_OIDC_CLIENT_ID`, `SCOS_OIDC_CLIENT_SECRET`, and `SCOS_OWNER_EMAIL` directly in the new Railway staging service settings. Never paste secrets in chat or commit them. The `scos-api` service needs the login secret; the renderer does not.
4. Complete Google sign-in yourself. This flow asks only `openid email profile`, not YouTube publishing or Meta access.
5. Complete a separate app-specific, scope-limited YouTube/Meta/AI/vidIQ setup after adapters and capability tests are ready. A Codex connector does not transfer its grants to this app. Paid calls stay blocked until a budget is explicitly set.
6. Run the authenticated staging browser/media workflow and remaining release gates. Production requires a separate owner release decision.

## Reproducible local verification of the branch

The original local app stays on ports 3100/8100 and database `scos_local`. This branch's browser suite uses ports 3101/8101 and `scos_e2e`.

```sh
uv sync --frozen
npm --prefix apps/web ci
make lint test-backend test-contracts build
uv run python scripts/prepare_e2e.py
# Start API and worker with SCOS_DATABASE_URL=.../scos_e2e and SCOS_S3_BUCKET=scos-e2e.
# Frontend: SCOS_API_URL=http://127.0.0.1:8101 npm --prefix apps/web run dev -- --port 3101
npm --prefix apps/web run test:e2e
```

Use the original local `make dev` instructions for the original release. Never point these test or migration commands at an existing production database. Test traces are synthetic/local only; remote traces are disabled by default to avoid recording session tokens.
