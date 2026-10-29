# Supabase migration and release gates

The original Mac checkout and GitHub `main` remain preserved at `175c5a5`. This migration is limited to the isolated staging branch and newly provisioned SCOS resources.

## Architecture

- Vercel preview frontend: `https://scos-staging-qwazi12.vercel.app`.
- Railway hosts the Python API and durable FFmpeg rendering worker.
- New Supabase project: `rceqkalcmixmejsfqkoy`, `screen-central-os-staging`, KY Media, `us-east-1`.
- PostgreSQL database: `postgres`, private schema `scos_staging`; the shared database's public schema is not used for application records.
- Browser database roles have no schema/table access. All application tables enable RLS. The dedicated `scos_staging_app` runtime role has explicit server policies and no RLS bypass; it is not the migration role.
- Supabase Storage bucket `scos-staging-media` is private. Uploads use `x-upsert=false`; duplicate content converges only after checksum verification. No hosted read depends on the worker filesystem.
- Owner Google sign-in uses Supabase PKCE, a single-use browser-bound verifier, server-side `/user` validation, the verified Google identity and configured owner allowlist. Provider tokens stay on the API server and are discarded after an opaque one-hour application session is issued.
- The before-user-created hook only accepts the configured owner email using Google. Email/phone/anonymous signup is disabled. The owner email and credentials are configured outside source control.

## Migrations

Alembic remains the source of application schema migrations. Supabase CLI migrations do not duplicate it. `scripts/migrate.py` uses a serialized advisory lock. The pooler can ignore startup `options`, so both runtime and migration connections explicitly select the schema; Alembic pins its version table to that schema.

Apply migrations once with the dedicated operator credential. Runtime services use `SCOS_MIGRATIONS_ON_START=false` and check the exact schema revision before startup. Runtime credentials cannot apply future DDL or silently skip an unapplied migration.

`scos_0004` adds RLS and removes browser-role privileges in private schemas. `scos_0005` adds the owner signup policy and hook. The original normative migration remains unchanged.

## Verification

79 backend tests passed, including owner identity/provider rejection, browser binding, single-use state, revoked-token rejection, private-bucket enforcement and non-overwriting upload behavior. Real Supabase checks verified the private schema, 47 RLS tables, restricted runtime permissions, private bucket, repeated immutable upload and SHA-256 readback. Two original staging media objects (518553 bytes) were copied and verified; the original Railway objects are retained.

The Vercel preview is ready and its API proxy was tested through Vercel's authenticated access. The deprecated CLI `--target` flag initially selected production in the isolated staging project; that build failed and never became ready. The corrected deployment explicitly uses `--environment preview`. Production promotion remains unapproved.

## Remaining gates

- Configure the Google provider in the new Supabase project and complete owner consent. Google must allow `https://rceqkalcmixmejsfqkoy.supabase.co/auth/v1/callback`.
- Supabase site URL is the canonical Vercel staging URL; application callback is `/api/v1/auth/supabase/callback`. The former Railway frontend and deployment-specific URLs redirect to the canonical hostname so login cookies remain bound to the same browser origin.
- Run the authenticated hosted browser → API → queue → worker → private storage → approval workflow after sign-in is available.
- Gemini drafting and priced budget settlement are implemented; see `GEMINI.md`. Paid calls remain disabled with a zero-dollar default until the owner's key and spending caps are configured and a real provider test passes. Social provider adapters/grants and remaining blueprint acceptance gates are still required.
- Hosted database/media backup and restore drills, monitoring, retention and the remaining full blueprint functionality must pass before production approval. Supabase database backups do not restore deleted Storage bytes; media needs independent retention/backups.

No existing Supabase project or legacy Scrapper resource is reused or modified. No provider secrets are sent to the frontend or committed.
