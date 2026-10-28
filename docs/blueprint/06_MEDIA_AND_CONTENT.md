# 06 — MEDIA, CREATIVE PRODUCTION, EXPORTS AND QUALITY ASSURANCE

## 1. Media architecture principle

**Original creative direction first.** Assets support the argument; the system must not generate a script solely to justify using whatever clips are available. A `ContentVariant` is an independently storyboarded piece, not a resized copy. All assets are immutable by content hash with explicit permission to use.

Use FFmpeg for probing/transcoding/loudness/cut detection and Remotion for deterministic edit compositions. Provide a `Renderer` interface so low-level composition techniques may be exchanged while keeping input/output and QA contracts stable.

## 2. Delivery profiles (our initial export templates, not asserted platform maxima)

| Format | Initial target | Audio / images | Creative principle |
|---|---|---|---|
| YouTube long-form | 1920×1080, 16:9, H.264 High, 30fps, MP4; duration selected by story | AAC stereo 48kHz; external thumbnail 1280×720 JPEG/PNG | Narrative progression, original insight, chapters only when useful |
| YouTube Short | 1080×1920, 9:16, H.264, 30fps MP4 | AAC 48kHz, embedded subtitles/optional separate captions | One strong idea, quick payoff and cut designed for vertical viewing |
| Instagram Reel | 1080×1920, 9:16 MP4, per-account provider validator | AAC 48kHz; platform-safe inset margins | Native hook, captions and no misleading recycled packaging |
| Facebook Reel | 1080×1920, 9:16 MP4, configured provider validated duration | AAC 48kHz; platform-aware caption | Standalone video and platform-specific description |
| Instagram carousel | 1080×1350 (4:5) slide sequence and/or 1080 square with consistent per-carousel geometry | 3–10 slides configurable, proofed on phone-size preview | Useful/savable, logical story progression |
| Static image post | 1080×1350 or 1080×1080; PNG/JPEG | Caption and alt text | News card, film comparison, question, original artwork |
| Text/community post | native provider text and optionally supported media | No media render required | Genuine question or information, not auto-engagement bait |
| Preview/QA | reduced bitrate matching final geometry | thumbnails, contact sheet, waveform, transcript | Fast human review and detect wrong export |

All platform limits (caption length, tag length, MIME, maximum duration, minimum resolution, media count, size, publishing permissions) are **capabilities looked up and validated per connector version and account**. Examples above are internal creative presets, not proofs of eligibility.

## 3. Content formats and mandatory creative structure

### A. “Moments Explained” Shorts/Reels
- Opening 0–2s: precise emotion/question or contextual surprise, not generic “You won't believe.”
- 2–8s: identify series/scene with enough context, avoid full copyrighted clip substitute.
- Middle: original interpretation, reason, comparison or overlooked detail; use approved factual evidence.
- Ending: real payoff or thoughtful question; no forced “subscribe” in every short.
- Each beat explicitly marks whether the visuals are source excerpts, original illustrations, charts, motion graphics or owner commentary.
- Tests: first 3 seconds meaningful without reading a full paragraph; visible captions do not obscure faces or platform controls; ending not truncated; audio audible at phone volume.

### B. “What We Know” release and trailer news
- Name the actual information need, state what is confirmed versus unconfirmed, cite current official sources.
- Avoid phantom trailers: if footage unavailable, use clearly labeled original stills/graphics and report that no official trailer was confirmed.
- Release date, theater/streamer status, regional differences, cast and credits independently checked.
- End with specific next question/known future milestone; no invented official date.

### C. “Worth Watching” rankings/countdowns
- Define the ranking criterion and inclusion/exclusion period; for subjective lists, label opinion.
- Each entry needs a clear distinct reason, evidence, one memorable insight, one original observation and suitable visuals.
- Do not force Top 15 if there are only 9 defensible candidates; owner must review change to Top 10 or smaller.
- Structure opener → premise/rubric → high-interest first item → varied progression → worthwhile #1 payoff → closing reflection. No filler to satisfy preselected minutes.
- Use original comparison graphics, quotes only when licensed/brief and legally appropriate, annotated visuals and transitions.

### D. Carousel / still / poll
- Each slide carries a headline with no invented claim; 3–10 slide sequence configurable; cover promises content, final panel offers context/source/appropriate invitation.
- Mobile preview at 360–420 CSS px width: no text clipping, small fonts, unsupported contrast, awkward crop, overlapping source credit.
- Image provenance preserved at slide level. Poll options are balanced, fact-based and not designed solely to provoke abuse.

### E. Cross-format campaign rules
- No automatic copying of entire long video into Reel; write a standalone vertical creative treatment.
- A campaign may yield zero, one or multiple format outputs based on owner-approved editorial brief. No forced content multiplication or duplicate publishing.
- Each variant must have a `format_reason` and unique content promise; reuse of source evidence is fine, repeating the identical artifact across several channels requires platform-specific review.

## 4. Asset acquisition and catalog contracts

### Allowed origins
1. Owner-created video/audio/photo and production graphics.
2. Licensed stock footage, purchased media, documented creator permission and platform-permitted remix under applicable rules.
3. Original generated images/audio when provider's output license covers intended commercial/public use and transparency rules are satisfied.
4. Official/provider metadata, links, press kits and source stills only under applicable separate use permissions.
5. Owner's Drive files shared with this separate new app; never import other Scrapper files unless owner explicitly authorizes.

### Reference-only discovery
- Monitor public YouTube accounts and creator channels for metadata, public stats and topic/hook analysis via compliant interfaces.
- Do not turn public reference URLs into automatic downloads, thumbnails to republish or raw media to store. In YouTube API policy, downloading/importing/backing up audiovisual content without YouTube's prior written approval is prohibited. Do not use residential proxy or authentication bypass mechanisms to circumvent restrictions.
- If provider terms restrict aggregating channel-level data or storing snapshots, disable that adapter or restrict to permissible views; use owner analytics instead.

### Ingest state machine
`source_submitted → metadata_verified → rights_review → upload_intent → bytes_received → quarantine → probed → checksum_verified → indexed → eligible | restricted | deleted`.
- Quarantine all untrusted uploads, enforce content-type/MIME/size quotas, reject decompression bombs, truncate extreme metadata, sanitize filenames and path segments.
- Server provides one short-lived PUT URL scoped to one object ID + expected size/type; never a bearer token granting entire bucket access.
- Upload complete handler verifies actual stored object hash and bytes before making asset visible.
- ffprobe in resource-limited worker, never shell-interpolate a user filename or URL. Parser errors are not success.
- Rights grant includes evidence, valid period, platform set, permitted use, derivatives, territory, monetization and attribution. If no grant covers target use, publishing ineligible.
- Storage shape: `assets/{sha256 prefix}/{asset_uuid}/original.ext`, `derived/{asset_uuid}/{analysis_version}/...`, `exports/{export_uuid}/{hash}.mp4`. Object key is server-generated; never derived directly from user title.

## 5. Catalog analysis and visual retrieval

For eligible media:
- Asset probe: duration, video streams, audio streams, fps, aspect, rotation, loudness, color primaries, bitrates, possible watermarks.
- Scene detection with adaptive cut thresholds; extract limited thumbnails and low-res proxies when permitted.
- Frame indexing: perceptual hash for nearby duplicate detection, descriptions from approved vision model, object/character candidates with uncertainty and confidence, setting, action, emotion, card/text detector, subtitle/OCR only where permitted.
- Audio: VAD, transcript with timestamps/speaker uncertainty, silence map, loudness map; no biometric voice matching or intrusive identification.
- Optional semantic retrieval: store embeddings only of authorized derived content and use Postgres full-text initially; add pgvector via separate migration if quality/scale warrant it.
- Retrieval scoring is transparent: `match(subject)`, `match(action)`, `match(setting)`, `image_quality`, `availability`, `rights`, `recency`, `reuse_count`, `caption_safe_zone`.
- No asset selected solely from a model hallucinated filename or claimed clip URL. Query may return “no eligible matching asset,” triggering original graphics or a new search.

## 6. Script and edit timing

- Script sentences carry stable IDs and factual claim IDs. Voice segments generated per sentence/beat; record actual duration using decoded waveform.
- Captions generated from final narration, word- or phrase-aligned, not estimated from text length alone. Spellcheck names, films and character roles using approved entities.
- Scene plan uses exact milliseconds. Validate `0 <= start < end <= source duration`, image still durations positive, no missing timeline interval unless intentionally black/silent with labeled intent.
- Music must have license, target medium and edit-use proof. Mix speech/music with loudness ducking; original music generation allowed only under appropriate license.
- Prioritize coherent pacing, not arbitrary frame changes. Slow narration can accompany deliberate pauses; silence only fails if unplanned.
- Text design accounts for platform overlays and mobile safe margins. Use text stroke/backdrop and WCAG-inspired contrast goals; subtitle templates subject to manual on-device review.
- Every template version and font reference is pinned in the brand kit. Never distribute font binaries in delivered documents.

## 7. Rendering lifecycle

1. Get `approved` script + versioned storyboard/claims/rights/asset references.
2. Validate output profile and calculate deterministic `input_snapshot_hash` over sorted dependency hashes + template/voice versions.
3. Acquire durable render job lease and budget/resource reservation.
4. Resolve source media via object store; checksum verify; copy into per-job isolated directory with disk cap.
5. Normalize audio/video streams, create supporting original graphics, render captions/voice/media composition.
6. Render low-cost preview first when editorial changes are likely; owner may approve preview direction.
7. Render final to temporary `*.partial` path; transcode to required profile; atomic upload to object store under immutable key; calculate SHA-256.
8. Probe actual output; generate contact sheet, subtitle overlays and waveform; perform automatic QA.
9. If pass, status `qa_passed` with owner pending; else `qa_failed` and issues/timestamps without altering previous exports.
10. On owner approval bind `export_sha256`, `input_snapshot_hash`, content revision, rights grant snapshot and publishing destination.

If job is interrupted, resume from last verifiable artifact (file + checksum), not from an unvalidated cache marker. Never replace an approved final video in place.

## 8. Technical media QA gates

| ID | Check | Initial policy / failure |
|---|---|---|
| QA-M01 | Video exists, >0 bytes, decodable with `ffprobe`/sample decode | Block on missing/corrupt |
| QA-M02 | Correct codec, pixel format, dimensions, rotation, fps, duration per selected profile | Block mismatched profile |
| QA-M03 | Audio track present when narration required, decodable, positive samples | Block missing or truncated audio |
| QA-M04 | Loudness/peak | Internal default target speech-led stereo around -16 LUFS ±2, true peak <= -1 dBTP; configurable per platform and audio style; block clipping, warn deviation |
| QA-M05 | Silence/gaps | Flag unplanned >0.6s narration gaps mid-beat; exclude intentional transitions; owner can approve deliberate silence |
| QA-M06 | Black/frozen segments | Flag unexpected sustained blank/frozen frames; correlate with intentional timeline markers; false positives reviewable |
| QA-M07 | Subtitle alignment | Each spoken segment overlaps corresponding caption with measured tolerance; no misspelled canonical names; no clipped/cut captions |
| QA-M08 | Visual matching | Sample shots match intended scene category or original illustration; weak confidence requests review, never falsely pass |
| QA-M09 | Repetition | Warn overused shots, identical video hash, repeated narration/sentences; editorial context decides |
| QA-M10 | Claim support | Every factual sentence resolves to currently approved claim/evidence version | Block |
| QA-M11 | Rights eligibility | Every used asset license covers the actual platform/territory/use and remains valid at schedule | Block if not |
| QA-M12 | Branding/legibility | Layout check and manual mobile-size preview; no overlap with safe zones | Block on objective clipping; manual aesthetic pass |
| QA-M13 | Disclosure/safety | Proper sponsor/AI/sensitive-content labels when applicable | Block missing required disclosures |
| QA-M14 | Publish package | Metadata length, thumbnail, media type and account capability valid | Block |

Objective checks are programmatic. Subjective content quality cannot be reliably certified by an LLM alone. Require at least one human/editorial signoff for production v1, with an explicit audited bypass mechanism only for tightly controlled future formats.

## 9. Media QA evidence artifacts

For every render save:
- `probe.json` (ffprobe stream/duration/codec data, source ID/hash).
- `audio_report.json` (loudness, peak, silence windows, narration duration).
- `frame_report.json` (black/frozen/subtitle-overflow findings with timestamps).
- `contact_sheet.jpg` (representative frames, no copyrighted external images beyond allowed usage).
- `subtitle_timing.json`, `caption_preview.mp4` or screenshots.
- `rights_snapshot.json` with exact grant IDs and validity at proposed publishing time.
- `claims_report.json` with factual sentence IDs, support evidence and unresolved issues.
- `qa_summary.json` including versions, warnings, blockers, reviewer actions and export hash.
- Optional video low-bitrate preview for browser.

All QA artifacts are private, signed-access and retention-scoped; they may contain sensitive unpublished drafts.

## 10. Brand kit (initial placeholders; not a user-approved identity)

Required brand kit fields: colors, safe text palette, title fonts, subtitle styles, transition library, icon system, original intro/outro, logo, end-card, pacing modes, spoiler label, citation style, music libraries and licensing, voice settings, variant profiles.

Do **not** assert an official Screen Central logo, font or voice unless user has uploaded/approved it. UI ships with neutral placeholders and an explicit brand-kit approval step. Templates must be reproducible when the original approved brand version is referenced.

## 11. Native content quality measurement and iteration

Track `render_attempts`, `time_to_preview`, `total_source_hours`, `editorial_edits`, `facts_rejected`, `repeated_shots_warned`, `qa_fail_rate`, `human_acceptance`, `publish_eligible_ratio` and `production_cost` per format. Optimize workflow efficiency only after media quality is acceptable. Never claim automated quality scores can predict virality.
