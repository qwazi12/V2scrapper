# 11 — CODEx BOOTSTRAP: ENTIRELY NEW PROJECT, NOT SCRAPPER

## Non-negotiable identity check

Existing application: `https://github.com/qwazi12/scrapper` — **DO NOT** clone, branch, fork, overwrite, modify or deploy that project for this build. It is not the new codebase. Any reused ideas require fresh implementation and licensing review; no credentials or data reuse without explicit authorization.

Proposed new application/repository: `https://github.com/qwazi12/screen-central-os` — this may not exist yet; create it as a **private, empty** repository after owner's approval. The specification does **not** assert that this URL currently exists.

Local working directory: `~/dev/screen-central-os` — separate from `~/dev/scrapper`.

## Option A — Bootstrap locally first

```bash
# Start from home; do not run inside ~/dev/scrapper
mkdir -p ~/dev/screen-central-os
cd ~/dev/screen-central-os
pwd
git init -b main
printf '# Screen Central OS\n\nIndependent greenfield application; NOT Scrapper.\n' > README.md
git add README.md
git commit -m 'chore: initialize independent Screen Central OS repo'

# Verify isolation before using Codex
git rev-parse --show-toplevel
git remote -v
# Expected: ~/dev/screen-central-os; no remote or only the NEW screen-central-os remote.
```

Unzip the accompanying `SCREEN_CENTRAL_OS_COMPLETE_BLUEPRINT_v1.zip` into a temporary directory and copy the specification into `docs/blueprint/` inside the new repository. **Do not put this blueprint inside Scrapper.**

If GitHub CLI is installed and authorized, create a **new private repository** manually after reviewing the repo name:

```bash
cd ~/dev/screen-central-os
gh repo create qwazi12/screen-central-os --private --source=. --remote=origin --push
# OR create via GitHub UI and then:
# git remote add origin https://github.com/qwazi12/screen-central-os.git
# git push -u origin main
```

The repo URL is an intended destination, not proof of an existing repo. Confirm current GitHub account is correct first.

Then launch Codex:

```bash
cd ~/dev/screen-central-os
pwd
git rev-parse --show-toplevel
git remote -v
git status --short
codex --cd "$PWD"
```

## Option B — Bootstrap after creating new empty remote

```bash
mkdir -p ~/dev
cd ~/dev
git clone https://github.com/qwazi12/screen-central-os.git
cd ~/dev/screen-central-os
pwd
git remote -v
codex --cd "$PWD"
```

Never use `codex github.com/qwazi12/scrapper` to select project. Codex CLI should start in the verified new checkout.

## Paste this into Codex for implementation

> **YOUR MISSION: BUILD A NEW PRODUCT, SCREEN CENTRAL OS, FROM THE ATTACHED COMPLETE BLUEPRINT.**
>
> Work ONLY in the new local repository `~/dev/screen-central-os` with remote `qwazi12/screen-central-os` if one has been explicitly created. This is a greenfield product; do NOT modify, fork, merge from, copy secrets from, deploy over, or interact with the data/services of `qwazi12/scrapper`.
>
> Read **every** file in `docs/blueprint/`, including `00_START_HERE.md`, product requirements, runtime architecture, full SQL, OpenAPI 3.1, AI/research contracts, content/media specs, publishing/analytics integration, security/ops, complete test strategy, and M0–M10 delivery backlog.
>
> First produce a compact architecture/consistency review, identify any contradictions or external blockers, and write an implementation task ledger in the new repo. Correct only real contract inconsistencies with a documented ADR; don't silently change requirements.
>
> Then implement milestones M0→M10 **in dependency order**. You are authorized to make routine local design, code, test and fixture decisions without asking after every change. Work in new-repo feature branches; keep changes small and reviewable. Do not auto-push or auto-merge unless I explicitly authorize it. Create frequent local commits and durable notes so interruptions are recoverable.
>
> **Build an actual working system.** Run a real local backend, Next.js frontend, PostgreSQL, object-storage emulator, job worker and media renderer. Use Playwright to interact with the UI. Generate original synthetic videos, previews and carousels; inspect real MP4s via ffprobe, audio and frame tests. Reproduce and fix failure cases. For EVERY bug, first create a failing regression test, then fix and rerun the actual affected end-to-end path.
>
> Keep provider adapters mocked until exact authorization, per-account capability and separate environment are available. NEVER send social posts, reply to real comments, connect production accounts, perform bulk external downloads, spend paid AI/API credits, create or deploy cloud resources, alter production configurations, or touch Scrapper without separate explicit approval. User accounts and media rights are not granted just because a URL or a previous app integration exists.
>
> When credentials or permission are missing, build the fully tested adapter and report it as `implemented_not_live_verified` or `blocked_by_external_approval`; continue with independent safe tasks. Never say it is working live based on mock success.
>
> Implement source-level evidence verification, fail-closed factual scripts, rights-aware asset selection, immutable export approvals, exactly-once local intent and external reconciliation, safe multi-platform packaging, comment reply approvals, provenance-tagged analytics and data-driven experiments. Track all costs and preserve a publishing kill switch that defaults OFF.
>
> **Required outputs** per milestone: commits and file diffs; test counts with pass/fail/skip/blocked; Playwright screenshot/trace; actual generated video/carousel path + hashes; ffprobe/caption/audio/QA reports; broken/unsupported integration list; environment/cost/security impact; next task. Keep the task ledger, ADRs and README up to date.
>
> The project is not done until every FR-001..FR-030 and AT-001..AT-060 is addressed, all core local/system tests pass and the exact user-visible workflows are verified. External integration prerequisites must remain explicit. Stop before production or real-account operations and request owner approval.
>
> Start with M0. Do not answer with another generic blueprint; start implementing and testing the new independent codebase.

## Minimum evidence for greenfield legitimacy

Before first substantial implementation PR:
- Check `pwd` and Git remote is **screen-central-os** only.
- Old Scrapper codebase not used as a scaffold, vendor directory or submodule.
- Brand-new `SCOS_` env namespace, separate PostgreSQL DB, local S3 mock bucket, isolated migrations.
- `README.md` contains *“not Scrapper”* project statement.
- CI fails when secrets, data source IDs, paths or callback URLs associated with Scrapper are accidentally introduced.
- Owner login and local smoke run with **zero external credentials**.

## Codex completion template

```text
MILESTONE: M[number] — [title]
BRANCH/COMMIT: [new repo only]
WORK COMPLETED: [files, API, migrations, UI, workers, docs]
TESTS: unit [x/y], integration [x/y], browser E2E [x/y], real media [x/y], security [x/y]
MOCKED PROVIDERS: [list]; LIVE READS: [list or none]; LIVE WRITES: none unless separately approved
MEDIA ARTIFACTS: [paths, sha256, ffprobe and contact sheets]
KNOWN ISSUES / BLOCKED: [exact blockers with severity]
COSTS: actual [usd] / reserved [usd] / unknown
SECURITY/RIGHTS: [approvals and failed gates]
EVIDENCE: [logs/traces/screenshots/test reports]
NEXT: [dependency-ordered tickets]
PRODUCTION: UNTOUCHED
SCRAPPER: UNTOUCHED
```

## Deliberate owner decisions required before production

1. Create/connect an entirely new official Google OAuth client, Meta app and provider credentials for SCOS.
2. Choose separate new production/staging domains, database and bucket credentials.
3. Upload and approve Screen Central brand kit/logo/fonts/voice and rights proof for each reusable media asset.
4. Approve a cost cap for paid model/media/provider operations; initial cap is zero.
5. Authorize each actual social account by immutable ID and enable publish individually.
6. Approve a controlled private/unlisted external upload, if needed, before full rollout.
7. Approve production activation; nothing in this blueprint itself changes live Scrapper or social behavior.

## Terminal safety helper

```bash
cd ~/dev/screen-central-os || exit 1
ROOT="$(git rev-parse --show-toplevel)"
printf 'ROOT=%s\n' "$ROOT"
case "$ROOT" in "$HOME/dev/screen-central-os") ;; *) echo 'WRONG REPOSITORY'; exit 2;; esac
if git remote -v | grep -qE 'qwazi12/scrapper(\.git)?([[:space:]]|$)'; then
  echo 'DANGER: Scrapper remote detected'; exit 3
fi
codex --cd "$ROOT"
```
