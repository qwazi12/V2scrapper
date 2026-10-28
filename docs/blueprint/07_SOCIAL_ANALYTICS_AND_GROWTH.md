# 07 — PLATFORM CONNECTORS, SOCIAL OPERATIONS, ANALYTICS AND GROWTH

## 1. External integration principle

**The provider's authenticated capability—not a static feature checklist—determines what the new app can actually do.** Every integration uses a separate SCOS OAuth client/account credential, scopes, refresh process, quota, health probe, dry-run validation, failure-state mapping and test fixtures. Do not reuse old Scrapper credentials, sessions, linked accounts or production pipelines.

Provider connector state: `unlinked → linking → linked_read_only → publish_authorized → healthy | degraded | expired | revoked`. `expired`/`revoked` blocks writes and displays reconnect action. `publish_authorized` does not itself turn publishing on: owner must enable it independently per account, with global kill switch also open.

### Capability matrix

| Platform | Read public/reference | Owner analytics | Video upload/publish | Reels/Shorts | Images/carousels | Comment reply |
|---|---|---|---|---|---|---|
| YouTube | API Data within policy | OAuth YouTube Analytics | `videos.insert`, resumable | Shorts determined by YouTube processing of eligible uploads | Thumbnail via supported endpoint; community posts not assumed API-accessible | Owner-authorized comments API |
| Instagram professional | Permitted Graph metadata | Scoped Insights, if eligible | Container creation/status then publish | IG Reel container | Image/carousel media containers where eligible | Scoped comment-management API |
| Facebook Page | Permitted Page information | Scoped Page/post insights, if eligible | Page video/photo/post endpoints | Facebook Page Reels multi-phase protocol | Image/text posts where granted; carousel unsupported unless documented for exact context | Scoped Page comment API |
| vidIQ | Only explicitly licensed/available integration surface | Its service may access own channel with separate auth | Not distribution by default | N/A | Not distribution | Not a substitute for platform account grants |
| Google Drive | Owner-authorized file metadata | N/A | Resumable upload archive | N/A | Archive only | N/A |

Do not claim that Facebook Groups, Instagram Stories, YouTube community polls, TikTok uploads or private-message automation are supported just because the UI can generate content for them. When unsupported, show a manual export package.

## 2. OAuth/security setup for each provider

- Use Authorization Code + PKCE where provider supports it; server-side confidential client only. CSRF/state and exact HTTPS callback URI, refresh-token lifecycle, server-side encrypted token store with key versions.
- Google: owner opts in separately to YouTube Data API write, YouTube Analytics read and Drive archive. App must pass necessary verification/audit policies for required scopes, and test with allowed account.
- Meta: create **new SCOS Meta app**, select a supported Login flow and permissions for linked professional Instagram/Facebook Page; complete permission review as required. Token validity, professional account eligibility and PPA status must be checked before writes.
- Account-binding sequence: OAuth → resolve platform account ID → show identity to owner → owner confirms target → run read-only capability probe → enable read sync → optional explicit publish activation after staging/production tests.
- Store external account `platform`, immutable platform ID, display name/handle, scopes, token expiry, capability snapshot, last health result. Never infer an account from display name alone.
- Scope permissions narrowly; record owner consent, connection and revocation events. Secrets are never logged or shown after entry.

## 3. YouTube connector specification

### Data
- Official YouTube Data API for metadata, own channel account, videos and comments. Public metadata subject to API service policies and data retention limits; monitor metadata-only and do not download/copy YouTube audiovisual files.
- Official YouTube Analytics API for owner channel; use `channel==MINE` or authorized channel ID with supported metric/dimension combinations.
- Video impressions/CTR metrics may require other authorized data sources/reports or manual Studio export; **do not claim every Studio metric is exposed in the core Analytics query API**. Display missing if unavailable.
- Reference channel monitoring must honor developer policies, including limits on cross-channel aggregation of API Data. Disable prohibited aggregation and prefer compliant, first-party vidIQ results where terms allow.

### Upload
1. Require `publish_ready` exact export, account capability, title/description/privacy checks; create persisted `publication_attempt` and reservation.
2. Initialize resumable upload via YouTube Data API `videos.insert`. Store secure session URI/receipt keyed by attempt ID; no secrets in logs.
3. Transfer in resumable chunks, query session state after ambiguous network failure. Upload the new video's content only once per unresolved attempt.
4. Record returned YouTube video ID and processing status; default `private` on first activation for an owner verification smoke test.
5. Apply authorized metadata/thumbnail operations with separate receipts and rate-limit awareness. A requested Short is still a video upload; classification and eligibility are enforced by YouTube, so verify actual observed outcome before labeling it a published Short.
6. Confirm remote video is attached to the intended channel and has the intended status. Only then `confirmed` and eligible to appear in the analytics correlation table.
7. Post-upload editing/replacement is distinct from duplicate uploading; never hide provider rejection by accepting a local success state.

**Specific Google documentation** (checked 2026-10-28): https://developers.google.com/youtube/data/reference/rest/v3/videos/insert , https://developers.google.com/youtube/data/guides/uploading_a_video , https://developers.google.com/youtube/analytics/channel_reports . Quota limits and API scope requirements are read from current developer documentation and verified against the app's project quota; no quota guessed from older blog posts.

### Comments
- Fetch `commentThreads.list`/`comments.list` where authorized and relevant; reply via `comments.insert` with owner approval and exact parent comment ID. Do not mass-comment, automatically like, or attempt to inflate engagement.
- Replies have their own unique operation intent/reconciliation; one approved reply cannot be sent twice after a lost response.

## 4. Instagram connector specification

**Preconditions:** supported Instagram Professional account, correct linked Page where that API flow requires it, permissions, active token, account eligible for content publishing, PPA completion if required, provider state healthy. API version pinned in provider adapter and revalidated regularly.

**Reels:**
1. Generate native vertical MP4 passing exact supported file/duration/codec rules; upload it to a short-lived provider-accessible HTTPS object URL scoped to that asset.
2. Create `/{ig_account_id}/media` with `media_type=REELS`, `video_url` and platform-tailored caption.
3. Persist returned media container ID as soon as request receipt is available.
4. Poll container `status_code` until `FINISHED` or terminal failure, bounded timeouts/backoff.
5. Write a separate final publish intent, then call `/{ig_account_id}/media_publish` using `creation_id`; reconcile unknown responses against container/account media if provider permits.
6. Store actual external media ID and publishing time. `container created` alone is **not** published.

**Images/carousels:** create individual children with carousel eligibility, create parent carousel container, poll readiness, call `media_publish`; enforce media count/format rules for current Graph version. For unsupported types, generate manual export instead of generic posting.

**Comments/insights:** use relevant permissions and supported Graph edges only; handle delayed/missing metrics; label the exact platform metric and revision.

**Official Meta maintained references:** https://www.postman.com/meta/instagram/documentation/6yqw8pt/instagram-api and https://developers.facebook.com/docs/instagram-platform/content-publishing/ . Credential model differs between Instagram Login and Facebook Login; select exactly one supported configuration per linked account instead of mixing token types.

## 5. Facebook Page connector specification

**Preconditions:** owner-authorized Page access token and Page permissions for publishing/engagement/insights, Page identity confirmed. Restrict scope to a Page rather than personal profile.

**Page Reel:** multi-phase upload (`video_reels`: start → upload file or hosted URL → status/processing → finish/publish). Store returned video ID and upload session separately from actual published status. The official Meta Postman Page Reel collection describes these phases: https://www.postman.com/meta/facebook/documentation/r56bjfd/facebook-api .

**Photo/text posts:** use supported Page APIs and permission probes; cap requests per account and check account-specific restrictions.

**Insights and comments:** preserve source metric names, compute time-windowed snapshots and reconcile deletions/permissions; do not assume cross-posting is equivalent to platform-native output.

**Do not** automatically repost a video when Facebook or Instagram succeeded but YouTube has not; each account/platform is independent and immutable intent is recorded.

## 6. vidIQ integration

- Treat vidIQ as **optional external intelligence**: keywords, competition, relative outliers, competitor concepts, title/thumbnail feedback and creator audience insights where its connected service provides them.
- The ability to use vidIQ in a ChatGPT conversation or in older Scrapper is not authorization for this **new** application's backend to call vidIQ. Verify a supported commercial API, connector or authenticated MCP runtime access first. If unavailable, provide authenticated CSV/JSON import and official YouTube API-derived read-only signals; do not scrape vidIQ's private web UI or reuse another app's secret.
- Rate/budget meter all vidIQ calls and store provenance: keyword/date/country/platform/estimated vs observed, cache TTL, score methodology where documented, original result ID.
- Do not use vidIQ score as factual truth or guarantee of virality. Video packaging acceptance remains based on honest promise and real channel data.

## 7. Drive archive implementation

- New OAuth/client or explicitly consented service account and a **new SCOS archive root folder**. Never write to Scrapper's existing Drive folders by default.
- Files stored in R2, only **approved exports / owner-authorized assets** are mirrored. Folder layout: `Screen Central OS/{Year}/{Campaign ID}/{Approved Exports}/{Platform Version}` and `Research Manifests`; no arbitrary raw creator rip catalog.
- Resumable Drive upload: persist intent and Drive session URI encrypted, complete upload, obtain ID, query metadata, verify size/checksum when supported, mark `verified`. Lost response reconciles using `appProperties` unique external intent key and folder/size; ambiguity becomes `unknown` hold—not duplicate upload.
- Never infer success from local file deletion. Remove temporary copy only after verified archive/object existence. No deletion of Drive objects as side-effect of clearing a posting row.
- Respect Drive quota, ownership, Shared Drive service accounts, and 429/5xx retries. Drive docs: https://developers.google.com/workspace/drive/api/guides/manage-uploads .

## 8. Publication transaction and reconciliation (normative)

`platform_package` contains exact `export_hash`, `account_id`, caption/title/tags/thumbnail/alt text, selected format, privacy, schedule, content hash and approval. Creation validates all fields against connector capability and rights; changes create package revision and void approval.

**Submission logic:**

```python
async def submit_safely(package_id, now):
    # transactional lock on package, export/account uniqueness and global flag
    intent = db.claim_due_approved_package(package_id, now, require_prod=True)
    if intent.existing_confirmed_or_unresolved:
        return intent.current_state  # no duplicate external write
    # mark intent/submitting durably BEFORE provider accepts anything
    db.record_attempt_intent(intent)
    try:
        receipt = await provider.begin(intent)
        db.save_receipt_and_processing_state(receipt)
    except DefinitelyRejected as e:
        db.reject_attempt(e)
    except (TimeoutError, UnknownOutcome):
        db.mark_unknown_for_reconciliation()
    # reconciliation uses provider read-only state BEFORE any retries
    return db.current_attempt(intent.id)
```

On process restart, scan `submitting`, `provider_processing`, `unknown` and lease-expired intent rows. Reconcile provider remote receipts using official API. If no safe correlation exists and the provider cannot establish absence, hold for human rather than re-submit. Exactly-once delivery is not guaranteed by arbitrary external APIs; our policy minimizes duplicates via durable intents and reconciliation.

### Post readiness checks
- Approved immutable export and package hashes match now.
- Source claim bundle and asset rights still valid at proposed post time.
- Account still linked, owner activated, correct platform ID and scopes, global kill switch open.
- Platform format constraints validated; privacy mode and disclosure verified.
- Cost/quota allowance and posting caps; no conflicting pending attempt; scheduled time in future or explicit publish-now.
- Relevant post copy unique enough and truthful; no repeated spam or prohibited automation.

### Default scheduling behavior
- Content enters draft/review. Owner explicitly chooses `Schedule` and account(s). No automatic queue insertion by Drive import or final render.
- Calendar uses owner time zone for display but all DB timestamps UTC; daylight savings resolved by IANA timezone library. Ambiguous local times require explicit offset/time resolution.
- Publishing priority favors reliability/quality rather than fixed 8x/day cadence. “Make video” does not mean “post video.”
- Owner can pause all new posts; in-progress provider submission may finish; UI shows the distinction.

## 9. Analytics data contracts

Each observation has: `platform`, `account_id`, `external_post_id`, `export_id`, `campaign_id`, `metric`, `unit`, `value/null`, numerator/denominator for derived rates, period_start, period_end, observed_at, ingested_at, provider_version, confidence, missing_reason, source and dimension. External data is immutable snapshots; late corrections append superseding observation not silently erase evidence.

**Metrics per platform are not directly additive** unless definitions and observation windows genuinely match. YouTube long-form views/engaged views, YouTube Shorts engaged views, Instagram plays/views, Facebook Reels plays, reach and impressions differ. Display native definitions and warn before comparative totals.

Core analysis queries:
- First 24h, 48h, 7d and 28d post publication measured by platform-specific calendar time and data freshness.
- Compare same-format cohorts of similar publication age; include zero/missing distinction, median and dispersion, not only mean. If a video has not reached 7 days, exclude from mature 7d baseline.
- Source-aware watch time/average view duration, retention and click-through metrics where officially exposed; no fabricated values.
- Per-campaign subscribers/followers gained, comments, shares, saves, conversions when provider actually reports them; no one-size-fits-all cross-platform conversion model.
- Total cost and cost per accepted export, production retries, publishing success/unknown rates, number of factual corrections.

**Privacy:** owner analytics private; comments deidentified for AI processing when possible; minimum necessary audience records; no inferred sensitive demographics or identity from comments. Allow comment deletion/tombstone updates.

## 10. Content choice, experimentation and learning

**Initial hypothesis rubric:** audience fit 25%, observed/estimated demand 20%, originality/payoff 20%, competitive gap 15%, timeliness 10%, feasible production/rights 10%. Score is a **decision aid**, not a predictive probability. Display underlying data, source date, unknowns, uncertainty and red-team rejection case. Factual/rights gates override ranking.

**Exploration:** target roughly 70% evidence-supported familiar series, 30% deliberately new ideas in initial test cycle—adjustable owner policy, not a guaranteed optimum. Compare by editorial family/format; do not publish content known to fail.

**Experiments:**
1. Pre-register hypothesis, scope, target audience/format, primary metric, window and kill criterion.
2. Generate truly different packages/treatments while holding other factors as constant as feasible. YouTube native thumbnail test may be used where available; never claim tool feedback score equals A/B result.
3. Schedule or publish within platform constraints and note confounders (topic, release timing, audience change, algorithm variation).
4. Wait for complete, comparable time window. Show sample size and missing data; for tiny observations return `inconclusive` instead of declaring winner.
5. Produce descriptive conclusion with alternative explanations and next inexpensive test. Update future recommendation weights only through versioned owner-approved model calibration.

**What not to do:** don't create spam, fake engagement, automatic mass comments, irrelevant replies, outrage bait, thumbnails promising scenes absent from the video, or unsupported growth claims.

## 11. Community workflow

- Sync own comments by platform-specific granted API only; capture thread ID, post ID, date, redacted text and owner-reply status. No demographic guessing.
- Classifier labels `question`, `correction`, `debate`, `suggestion`, `praise`, `criticism`, `spam`, `other` with confidence/uncertainty; important factual correction becomes research incident candidate.
- Generate suggested responses from content context, label AI draft. Owner edits/approves exact content, parent comment/account; publish once with receipt. No auto-approval of all replies.
- Duplicate/repeat commenters and harassment are handled through normal moderation controls and platform terms; do not automate abusive replies.
- Summarize recurrent themes as opportunity candidates with sample sizes, representative deidentified questions and time window; avoid reading isolated comments as population-level demand.

## 12. Monitoring and on-call playbooks

Alert on expired grant, empty analytics sync, unexpected 401/403/429, unknown publication >60min, repeated errors, observed unexpected destination, high media QA failure, budget >80%/100%, source outage, repeated content dedupe, and user-reported factual correction. Each alert contains actionable route to correct record; no full tokens or sensitive comment contents included in notifications.

Before reauthorization, inspect token status, OAuth client config and scopes, do not repeatedly retry revoked grants. Before posting retry, reconcile remote account. Before content correction, inspect research evidence and publication status.
