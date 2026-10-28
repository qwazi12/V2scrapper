# Verification ledger — local release 0.1

Date: 2026-10-28. Local Mac execution. No real social account, OAuth grant, paid model call or cloud deployment used.

## Automated checks

- Backend: **42 passed, 0 failed, 0 skipped** in 13.83 seconds; isolated `scos_test` PostgreSQL database and local S3 emulator. JUnit: `artifacts/backend-tests.xml`.
- Warning: current Starlette emits a TestClient/httpx deprecation warning. Tests pass; migration to its future recommended test transport remains maintenance work.
- Ruff: passed on API and scripts. TypeScript project typecheck: passed. Optimized Next.js build: passed. Development and production build directories are separated to keep build verification from disturbing preview.
- Reference and runtime OpenAPI: both validate. **27 of 89 reference paths present**. This is path inventory only, not exact full schema conformance. Runtime local command endpoints are explicit extensions. Coverage file: `contract-coverage.json`.
- Actual media: 3 immutable exports independently SHA-256 verified. Both MP4s fully decoded with FFmpeg and probed for correct dimensions/H.264/AAC; carousel ZIP opened and each PNG checked. No substituted/fake MP4s in these artifacts.
- Restore: `scos_restore_20261028214925` restored from pg_dump into a new isolated database; 3 export identities/hashes and 1 publication attempt matched. No worker attached to recovery DB. A later UI reconciliation changed the live local attempt from unknown to confirmed; the earlier recovery snapshot intentionally preserves its earlier state.

## Real browser checks

Performed through the served Next.js application in the in-app browser:

1. Local owner sign-in; workspace data loaded from actual API/PostgreSQL.
2. Created original fictional fixture through Control Room.
3. Unreviewed research approval failed with CLAIM_UNVERIFIED.
4. Inspected exact passages; reviewed both claims; approved the hashed research package.
5. Created campaign, independent landscape/portrait/carousel drafts; approved exact script hashes.
6. Queued all three renders through UI. Separate worker produced actual media.
7. Quality Review displayed actual carousel and QA. Portrait video metadata in browser: readyState 4, duration 15 seconds, 1080×1920, no error. After keyboard playback, currentTime advanced to 5.02 seconds with paused=false.
8. Approved carousel and portrait as explicitly labeled automated synthetic test approvals, not owner commercial editorial signoff.
9. Created exact mock YouTube package; simulated provider acceptance with lost acknowledgment. UI held unknown. Reconciliation produced confirmed post ID with submit_count=1; no retry.
10. Imported deidentified test comments; saved one reply, approved exact text and confirmed individual mock send.
11. Imported synthetic analytics; separate platform panels, unavailable average view duration displayed Unknown with explanation.
12. Pre-registered one experiment; conclusion remains inconclusive.
13. Clean `make dev` restart retained application state, session and playable media through the local object mirror.
14. Mobile at 375×812: document width 360 (scrollbar), no horizontal overflow; navigation worked. New-idea dialog focused working title; Escape dismissed it. Desktop checked at 1440×1000. Browser console error log empty after final checks.

The browser checks are an observed manual automation run, not a committed automated Playwright test suite. Full AT-001..060 and production provider acceptance remain incomplete. No human audio/editorial commercial approval was claimed. Caption safe area is currently a constrained renderer-layout check, not full OCR/frame-based caption inspection.

## Actual generated media

| Format | Dimensions / duration | SHA-256 |
|---|---|---|
| Landscape | 1920×1080 / 20s | f368850685f2c7c6007a4e60368f6b43ddf44a6a41b95bb91de0b186fc425dc0 |
| Portrait | 1080×1920 / 15s | 5b2de65a1d05d58b432a13cd320515397871d31493cc11748a5ee0276b389c72 |
| Carousel ZIP | 3 PNGs / 1080×1350 | 782ea31cd0c7647c9e9acad38d504ca51dc8243c1324ea401b4bdfe1b94d8b9c |

Media is wholly fictional, original geometric test content with local synthetic speech. It does not claim to be real movie news or a finished Screen Central brand treatment.
