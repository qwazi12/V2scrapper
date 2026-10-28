-- SCREEN CENTRAL OS, GREENFIELD INITIAL MIGRATION
-- PostgreSQL >=16, schema version scos_0001. This is NOT a migration of Scrapper.
-- Later changes MUST use Alembic migrations. Every table is owned by this new app/database.
BEGIN;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Identity, authorization, capability. Single owner at launch, tables allow approved editors later.
CREATE TABLE app_users (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), email text NOT NULL UNIQUE,
 display_name text NOT NULL, role text NOT NULL DEFAULT 'owner' CHECK(role IN ('owner','editor','viewer')),
 auth_subject text NOT NULL UNIQUE, active boolean NOT NULL DEFAULT true,
 created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE sessions (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), user_id uuid NOT NULL REFERENCES app_users(id) ON DELETE CASCADE,
 token_hash bytea NOT NULL UNIQUE, csrf_hash bytea NOT NULL,
 expires_at timestamptz NOT NULL, revoked_at timestamptz,
 created_at timestamptz NOT NULL DEFAULT now(), last_seen_at timestamptz
);
CREATE INDEX idx_sessions_active ON sessions(user_id, expires_at) WHERE revoked_at IS NULL;
CREATE TABLE oauth_grants (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), provider text NOT NULL,
 external_subject text NOT NULL, owner_user_id uuid NOT NULL REFERENCES app_users(id),
 encrypted_access_token bytea NOT NULL, encrypted_refresh_token bytea,
 key_version integer NOT NULL, scopes text[] NOT NULL DEFAULT '{}', expires_at timestamptz,
 status text NOT NULL DEFAULT 'active' CHECK(status IN ('active','expired','revoked','error')),
 last_verified_at timestamptz, created_at timestamptz NOT NULL DEFAULT now(),
 updated_at timestamptz NOT NULL DEFAULT now(), UNIQUE(provider, external_subject)
);
CREATE TABLE social_accounts (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), grant_id uuid REFERENCES oauth_grants(id),
 platform text NOT NULL CHECK(platform IN ('youtube','instagram','facebook','other')),
 external_account_id text NOT NULL, display_name text NOT NULL, handle text,
 publish_enabled boolean NOT NULL DEFAULT false, read_enabled boolean NOT NULL DEFAULT false,
 capability_snapshot jsonb NOT NULL DEFAULT '{}'::jsonb,
 capability_verified_at timestamptz, connected_at timestamptz NOT NULL DEFAULT now(),
 disconnected_at timestamptz, UNIQUE(platform,external_account_id)
);
CREATE TABLE feature_flags (
 name text NOT NULL, environment text NOT NULL CHECK(environment IN ('local','ci','staging','production')),
 enabled boolean NOT NULL DEFAULT false, reason text, updated_by uuid REFERENCES app_users(id),
 updated_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY(name,environment)
);
CREATE TABLE brand_kits (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), name text NOT NULL, revision integer NOT NULL DEFAULT 1,
 settings jsonb NOT NULL, is_active boolean NOT NULL DEFAULT false,
 sha256 text NOT NULL CHECK(length(sha256)=64), created_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(name,revision)
);

-- Discovery, external identities, reference monitors.
CREATE TABLE external_entities (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), entity_type text NOT NULL CHECK(entity_type IN ('film','tv','season','episode','person','character','source_channel')),
 canonical_provider text, canonical_id text,
 name text NOT NULL, year integer, aliases text[] NOT NULL DEFAULT '{}',
 metadata jsonb NOT NULL DEFAULT '{}'::jsonb, updated_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(canonical_provider,canonical_id)
);
CREATE TABLE source_monitors (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), provider text NOT NULL,
 external_id text NOT NULL, canonical_url text NOT NULL, subject text NOT NULL,
 scope text NOT NULL DEFAULT 'metadata_only', last_cursor text, last_checked_at timestamptz,
 enabled boolean NOT NULL DEFAULT true, filters jsonb NOT NULL DEFAULT '{}'::jsonb,
 UNIQUE(provider,external_id)
);
CREATE TABLE opportunities (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), title text NOT NULL,
 angle text, audience_hypothesis text NOT NULL, payoff text, why_us text,
 status text NOT NULL DEFAULT 'new' CHECK(status IN ('new','triaged','research_pending','researching','researched','accepted','rejected','deferred')),
 priority integer NOT NULL DEFAULT 0, owner_decision text, owner_decision_at timestamptz,
 rationale jsonb NOT NULL DEFAULT '{}'::jsonb, revision integer NOT NULL DEFAULT 1,
 dedupe_fingerprint text UNIQUE, created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE opportunity_signals (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), opportunity_id uuid NOT NULL REFERENCES opportunities(id) ON DELETE CASCADE,
 source_name text NOT NULL, measurement_kind text NOT NULL, observed_at timestamptz,
 period_start timestamptz, period_end timestamptz, value numeric(22,6), units text,
 evidence_url text, evidence_ref text, confidence text NOT NULL DEFAULT 'unknown'
 CHECK(confidence IN ('observed','estimated','heuristic','opinion','unknown')),
 payload jsonb NOT NULL DEFAULT '{}'::jsonb, recorded_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_opportunity_signals ON opportunity_signals(opportunity_id, recorded_at DESC);

-- Research evidence. External source text is treated as untrusted data, NEVER instructions.
CREATE TABLE source_records (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), provider text NOT NULL, uri text NOT NULL,
 retrieved_at timestamptz NOT NULL DEFAULT now(), published_at timestamptz,
 source_kind text NOT NULL DEFAULT 'web', trust_class text NOT NULL DEFAULT 'unclassified',
 author_org text, title text, snippet text, content_sha256 text, object_key text,
 rights_to_store text NOT NULL DEFAULT 'metadata_only', expires_at timestamptz,
 fetch_status text NOT NULL DEFAULT 'ok', metadata jsonb NOT NULL DEFAULT '{}'::jsonb
);
CREATE INDEX idx_source_uri ON source_records(uri, retrieved_at DESC);
CREATE TABLE claims (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), opportunity_id uuid REFERENCES opportunities(id),
 subject_entity_id uuid REFERENCES external_entities(id),
 text text NOT NULL, kind text NOT NULL,
 epistemic_type text NOT NULL CHECK(epistemic_type IN ('fact','inference','opinion','rumor','unknown')),
 status text NOT NULL DEFAULT 'proposed' CHECK(status IN ('proposed','evidence_pending','supported','contradicted','uncertain','rejected')),
 factual_value jsonb, valid_from timestamptz, valid_to timestamptz,
 revision integer NOT NULL DEFAULT 1, last_adjudicated_at timestamptz,
 created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_claims_opportunity_status ON claims(opportunity_id,status);
CREATE TABLE claim_evidence (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), claim_id uuid NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
 source_id uuid NOT NULL REFERENCES source_records(id),
 stance text NOT NULL CHECK(stance IN ('supports','contradicts','mentions','unknown')),
 locator text NOT NULL, excerpt text, structured_field text,
 evidence_scope text NOT NULL DEFAULT 'exact_statement',
 review_method text NOT NULL DEFAULT 'human_or_structured_check',
 reviewer_user_id uuid REFERENCES app_users(id), reviewed_at timestamptz,
 notes text, UNIQUE(claim_id,source_id,locator,stance)
);
CREATE INDEX idx_claim_evidence_claim ON claim_evidence(claim_id,stance);
CREATE TABLE research_packages (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), opportunity_id uuid NOT NULL REFERENCES opportunities(id),
 revision integer NOT NULL, claim_ids uuid[] NOT NULL DEFAULT '{}', source_ids uuid[] NOT NULL DEFAULT '{}',
 policy_version text NOT NULL, summary text NOT NULL, risk_notes text,
 content_hash text NOT NULL CHECK(length(content_hash)=64),
 status text NOT NULL DEFAULT 'draft' CHECK(status IN ('draft','blocked','approved','revoked')),
 approved_by uuid REFERENCES app_users(id), approved_at timestamptz,
 created_at timestamptz NOT NULL DEFAULT now(), UNIQUE(opportunity_id,revision), UNIQUE(content_hash)
);

-- Campaign, versions, original treatments, storyboards.
CREATE TABLE campaigns (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), opportunity_id uuid REFERENCES opportunities(id),
 research_package_id uuid NOT NULL REFERENCES research_packages(id),
 title text NOT NULL, series_name text, viewer_promise text NOT NULL, original_angle text NOT NULL,
 primary_audience text, spoiler_policy text NOT NULL DEFAULT 'mark',
 status text NOT NULL DEFAULT 'draft' CHECK(status IN ('draft','brief_review','brief_approved','producing','qa_pending','qa_failed','ready_for_approval','approved','published','archived')),
 revision integer NOT NULL DEFAULT 1, created_by uuid REFERENCES app_users(id),
 created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE campaign_variants (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), campaign_id uuid NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
 format text NOT NULL CHECK(format IN ('long_16_9','short_9_16','reel_9_16','carousel_4_5','image_1_1','story_9_16','text_post')),
 angle text NOT NULL, intended_platform text, target_duration_ms integer CHECK(target_duration_ms>0),
 script_revision integer NOT NULL DEFAULT 1, approved_storyboard_hash text,
 config jsonb NOT NULL DEFAULT '{}'::jsonb, status text NOT NULL DEFAULT 'draft',
 created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE scripts (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), variant_id uuid NOT NULL REFERENCES campaign_variants(id) ON DELETE CASCADE,
 revision integer NOT NULL, text text NOT NULL, sentences jsonb NOT NULL,
 claim_ids uuid[] NOT NULL DEFAULT '{}', text_sha256 text NOT NULL CHECK(length(text_sha256)=64),
 review_status text NOT NULL DEFAULT 'draft' CHECK(review_status IN ('draft','blocked','verified','owner_approved','revoked')),
 approved_by uuid REFERENCES app_users(id), approved_at timestamptz,
 created_at timestamptz NOT NULL DEFAULT now(), UNIQUE(variant_id,revision)
);

-- Asset identity, rights and immutable media.
CREATE TABLE media_assets (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), kind text NOT NULL CHECK(kind IN ('video','image','audio','subtitle','transcript','font','document','other')),
 origin_type text NOT NULL, source_uri text, external_provider text, external_id text,
 filename text NOT NULL, media_type text, sha256 text NOT NULL CHECK(length(sha256)=64),
 byte_size bigint NOT NULL CHECK(byte_size>=0), object_key text NOT NULL UNIQUE,
 duration_ms bigint, width integer, height integer, frame_rate numeric(10,4),
 status text NOT NULL DEFAULT 'quarantine' CHECK(status IN ('quarantine','processing','approved','restricted','deleted')),
 metadata jsonb NOT NULL DEFAULT '{}'::jsonb, created_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(sha256,kind)
);
CREATE TABLE asset_rights (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), asset_id uuid NOT NULL REFERENCES media_assets(id) ON DELETE CASCADE,
 rights_kind text NOT NULL CHECK(rights_kind IN ('owner_created','licensed','provider_permitted','reference_only','pending','prohibited')),
 rights_holder text, proof_object_key text, grant_uri text,
 valid_from timestamptz, valid_to timestamptz,
 platforms text[] NOT NULL DEFAULT '{}', permitted_uses text[] NOT NULL DEFAULT '{}',
 derivatives_allowed boolean NOT NULL DEFAULT false, monetization_allowed boolean,
 territory text, attribution text, reviewed_by uuid REFERENCES app_users(id), reviewed_at timestamptz,
 notes text, created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_rights_asset ON asset_rights(asset_id,valid_to);
CREATE TABLE asset_scenes (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), asset_id uuid NOT NULL REFERENCES media_assets(id) ON DELETE CASCADE,
 start_ms bigint NOT NULL CHECK(start_ms>=0), end_ms bigint NOT NULL,
 description text, transcript text, visual_tags text[] NOT NULL DEFAULT '{}',
 analysis_version text, confidence numeric(5,4) CHECK(confidence BETWEEN 0 AND 1),
 embedding_model text, embedding jsonb, -- optional vector index is a later migration; never an uninstalled extension
 CHECK(end_ms>start_ms)
);
CREATE TABLE asset_usage (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), variant_id uuid NOT NULL REFERENCES campaign_variants(id),
 asset_id uuid NOT NULL REFERENCES media_assets(id), rights_id uuid REFERENCES asset_rights(id),
 scene_id uuid REFERENCES asset_scenes(id), use_kind text NOT NULL,
 timeline_start_ms bigint NOT NULL DEFAULT 0, timeline_end_ms bigint NOT NULL,
 attribution_rendered boolean NOT NULL DEFAULT false,
 CHECK(timeline_end_ms > timeline_start_ms)
);

-- Worker jobs, immutable exports and QA.
CREATE TABLE jobs (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), kind text NOT NULL, aggregate_kind text, aggregate_id uuid,
 input_hash text NOT NULL, payload jsonb NOT NULL,
 status text NOT NULL DEFAULT 'queued' CHECK(status IN ('queued','leased','running','succeeded','retry_wait','blocked','failed','cancelled','dead_letter')),
 priority integer NOT NULL DEFAULT 0, available_at timestamptz NOT NULL DEFAULT now(),
 lease_owner text, lease_epoch bigint NOT NULL DEFAULT 0, lease_expires_at timestamptz,
 heartbeat_at timestamptz, attempt_count integer NOT NULL DEFAULT 0,
 max_attempts integer NOT NULL DEFAULT 3, last_error_code text, last_error_summary text,
 output jsonb, created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(),
 CHECK(attempt_count>=0), CHECK(max_attempts>=0)
);
CREATE INDEX idx_jobs_claim ON jobs(status,available_at,priority DESC,created_at);
CREATE INDEX idx_jobs_lease ON jobs(lease_expires_at) WHERE status IN ('leased','running');
CREATE TABLE job_events (
 id bigserial PRIMARY KEY, job_id uuid NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
 stage text NOT NULL, event_type text NOT NULL, progress numeric(5,2),
 message text, detail jsonb NOT NULL DEFAULT '{}'::jsonb, created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_job_events ON job_events(job_id,id);
CREATE TABLE exports (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), variant_id uuid NOT NULL REFERENCES campaign_variants(id),
 job_id uuid REFERENCES jobs(id), format text NOT NULL,
 object_key text NOT NULL UNIQUE, sha256 text NOT NULL CHECK(length(sha256)=64),
 byte_size bigint NOT NULL CHECK(byte_size>=0), duration_ms bigint,
 width integer, height integer, codec jsonb,
 input_snapshot_hash text NOT NULL CHECK(length(input_snapshot_hash)=64),
 status text NOT NULL DEFAULT 'rendered' CHECK(status IN ('requested','queued','running','rendered','qa_failed','qa_passed','approved','available','revoked')),
 created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_exports_variant ON exports(variant_id,created_at DESC);
CREATE TABLE quality_checks (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), export_id uuid NOT NULL REFERENCES exports(id) ON DELETE CASCADE,
 check_name text NOT NULL, severity text NOT NULL CHECK(severity IN ('blocker','warning','info')),
 status text NOT NULL CHECK(status IN ('pass','fail','inconclusive','skipped')),
 evidence_key text, observed_value jsonb, threshold jsonb, checker_version text NOT NULL,
 executed_at timestamptz NOT NULL DEFAULT now(), UNIQUE(export_id,check_name,checker_version)
);
CREATE TABLE export_approvals (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), export_id uuid NOT NULL REFERENCES exports(id),
 export_sha256 text NOT NULL, input_snapshot_hash text NOT NULL,
 approval_kind text NOT NULL CHECK(approval_kind IN ('editorial','rights','publish_ready')),
 status text NOT NULL DEFAULT 'approved' CHECK(status IN ('approved','revoked')),
 approved_by uuid NOT NULL REFERENCES app_users(id), approved_at timestamptz NOT NULL DEFAULT now(),
 revoked_at timestamptz, notes text,
 UNIQUE(export_id,approval_kind,approved_at)
);

-- Platform output packages, transactional intent, external submission receipts.
CREATE TABLE platform_packages (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), export_id uuid NOT NULL REFERENCES exports(id),
 account_id uuid NOT NULL REFERENCES social_accounts(id),
 title text, caption text, tags text[] NOT NULL DEFAULT '{}',
 thumbnail_asset_id uuid REFERENCES media_assets(id), alt_text text,
 revision integer NOT NULL DEFAULT 1,
 content_hash text NOT NULL CHECK(length(content_hash)=64),
 status text NOT NULL DEFAULT 'draft' CHECK(status IN ('draft','validated','approved','revoked')),
 approved_by uuid REFERENCES app_users(id), approved_at timestamptz,
 scheduled_at timestamptz, created_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(export_id,account_id,revision)
);
CREATE TABLE publication_attempts (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), package_id uuid NOT NULL REFERENCES platform_packages(id),
 account_id uuid NOT NULL REFERENCES social_accounts(id), export_id uuid NOT NULL REFERENCES exports(id),
 dedupe_key text NOT NULL, attempt_no integer NOT NULL DEFAULT 1,
 parent_attempt_id uuid REFERENCES publication_attempts(id),
 state text NOT NULL DEFAULT 'draft' CHECK(state IN ('draft','scheduled','claimed','submitting','provider_processing','confirmed','rejected','unknown','cancelled')),
 external_request_id text, external_container_id text, external_post_id text,
 provider_status jsonb NOT NULL DEFAULT '{}'::jsonb,
 not_before timestamptz, submitted_at timestamptz, confirmed_at timestamptz,
 last_checked_at timestamptz, error_code text, error_summary text,
 created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(dedupe_key,attempt_no)
);
-- Prevent a second unfinished submission for the same immutable export/account, even if package changes.
CREATE UNIQUE INDEX idx_one_unresolved_publication ON publication_attempts(export_id,account_id)
 WHERE state IN ('scheduled','claimed','submitting','provider_processing','unknown');
CREATE UNIQUE INDEX idx_external_confirmed ON publication_attempts(account_id,external_post_id)
 WHERE external_post_id IS NOT NULL;
-- Once export X has been confirmed on account Y, no second confirmation of that same pair is valid.
-- The domain service ALSO refuses a new attempt if a confirmed row already exists, *before* any external call.
CREATE UNIQUE INDEX idx_one_confirmed_publication ON publication_attempts(export_id,account_id)
 WHERE state='confirmed';
CREATE INDEX idx_publication_due ON publication_attempts(state,not_before) WHERE state='scheduled';
CREATE TABLE publication_events (
 id bigserial PRIMARY KEY, attempt_id uuid NOT NULL REFERENCES publication_attempts(id) ON DELETE CASCADE,
 kind text NOT NULL, sanitized_response jsonb, created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE archive_exports (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), export_id uuid NOT NULL REFERENCES exports(id),
 destination text NOT NULL CHECK(destination IN ('drive','other')),
 folder_id text, file_id text, external_intent_key text NOT NULL UNIQUE,
 upload_session_ciphertext bytea, sha256 text NOT NULL,
 state text NOT NULL DEFAULT 'intent' CHECK(state IN ('intent','uploading','verifying','verified','unknown','failed')),
 byte_size bigint NOT NULL, last_checked_at timestamptz, created_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(destination,file_id)
);

-- Community and analytics.
CREATE TABLE comment_threads (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), account_id uuid NOT NULL REFERENCES social_accounts(id),
 external_thread_id text NOT NULL, external_post_id text,
 topic text, category text, status text NOT NULL DEFAULT 'unreviewed',
 summary text, anonymized_author_ref text,
 first_seen_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(account_id,external_thread_id)
);
CREATE TABLE comment_messages (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), thread_id uuid NOT NULL REFERENCES comment_threads(id) ON DELETE CASCADE,
 external_comment_id text NOT NULL, author_kind text NOT NULL DEFAULT 'viewer',
 encrypted_raw_text bytea, redacted_text text,
 posted_at timestamptz, imported_at timestamptz NOT NULL DEFAULT now(),
 status text NOT NULL DEFAULT 'visible', UNIQUE(thread_id,external_comment_id)
);
CREATE TABLE reply_drafts (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), thread_id uuid NOT NULL REFERENCES comment_threads(id),
 parent_comment_id text NOT NULL, draft_text text NOT NULL,
 draft_hash text NOT NULL CHECK(length(draft_hash)=64),
 state text NOT NULL DEFAULT 'draft' CHECK(state IN ('draft','review','approved','sending','confirmed','unknown','rejected')),
 approved_by uuid REFERENCES app_users(id), approved_at timestamptz,
 external_reply_id text, sent_at timestamptz, last_error text,
 created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE analytics_observations (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), account_id uuid NOT NULL REFERENCES social_accounts(id),
 external_post_id text, campaign_id uuid REFERENCES campaigns(id), export_id uuid REFERENCES exports(id),
 platform text NOT NULL, metric text NOT NULL,
 value numeric(25,6), numerator numeric(25,6), denominator numeric(25,6),
 unit text NOT NULL, dimension jsonb NOT NULL DEFAULT '{}'::jsonb,
 period_start timestamptz NOT NULL, period_end timestamptz NOT NULL,
 observed_at timestamptz NOT NULL, ingested_at timestamptz NOT NULL DEFAULT now(),
 source text NOT NULL, source_row_hash text NOT NULL,
 confidence text NOT NULL DEFAULT 'observed' CHECK(confidence IN ('observed','estimated','heuristic','unknown')),
 data_delay_hours integer, missing_reason text,
 CHECK(period_end>period_start), UNIQUE(account_id,metric,period_start,period_end,source_row_hash)
);
CREATE INDEX idx_metrics_campaign ON analytics_observations(campaign_id,metric,period_end DESC);
CREATE TABLE experiments (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), campaign_id uuid REFERENCES campaigns(id),
 name text NOT NULL, hypothesis text NOT NULL, primary_metric text NOT NULL,
 success_criterion text NOT NULL, cohort_rules jsonb NOT NULL,
 state text NOT NULL DEFAULT 'planned' CHECK(state IN ('planned','running','analyzing','concluded','cancelled')),
 protocol_version text NOT NULL, pre_registered_at timestamptz NOT NULL DEFAULT now(),
 conclusion text, confidence_note text, concluded_at timestamptz
);
CREATE TABLE experiment_arms (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), experiment_id uuid NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
 arm_name text NOT NULL, package_id uuid REFERENCES platform_packages(id),
 creative_version_hash text NOT NULL, planned_sample integer, actual_sample integer,
 UNIQUE(experiment_id,arm_name)
);

-- Finance, auditable operation history, durable events.
CREATE TABLE budget_policies (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), policy_key text NOT NULL UNIQUE,
 currency char(3) NOT NULL DEFAULT 'USD', period text NOT NULL CHECK(period IN ('daily','monthly','campaign')),
 limit_amount numeric(18,6) NOT NULL CHECK(limit_amount>=0),
 consumed_amount numeric(18,6) NOT NULL DEFAULT 0 CHECK(consumed_amount>=0),
 reserved_amount numeric(18,6) NOT NULL DEFAULT 0 CHECK(reserved_amount>=0),
 reset_at timestamptz, enabled boolean NOT NULL DEFAULT true,
 updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE cost_reservations (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), policy_id uuid NOT NULL REFERENCES budget_policies(id),
 job_id uuid REFERENCES jobs(id), amount_reserved numeric(18,6) NOT NULL CHECK(amount_reserved>=0),
 amount_actual numeric(18,6), state text NOT NULL DEFAULT 'active' CHECK(state IN ('active','settled','released','unknown')),
 created_at timestamptz NOT NULL DEFAULT now(), settled_at timestamptz
);
CREATE TABLE cost_events (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), job_id uuid REFERENCES jobs(id),
 reservation_id uuid REFERENCES cost_reservations(id), provider text NOT NULL,
 model_or_service text, operation text NOT NULL, amount_usd numeric(18,6) CHECK(amount_usd>=0),
 request_units jsonb, provider_receipt text, observed_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE domain_events (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), aggregate_kind text NOT NULL, aggregate_id uuid NOT NULL,
 aggregate_revision integer NOT NULL, event_type text NOT NULL, schema_version integer NOT NULL DEFAULT 1,
 payload jsonb NOT NULL, delivered_at timestamptz,
 delivery_attempts integer NOT NULL DEFAULT 0, available_at timestamptz NOT NULL DEFAULT now(),
 last_error text, created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_domain_events_ready ON domain_events(available_at,created_at) WHERE delivered_at IS NULL;
CREATE TABLE event_inbox_receipts (
 subscriber text NOT NULL, event_id uuid NOT NULL REFERENCES domain_events(id),
 received_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY(subscriber,event_id)
);
CREATE TABLE idempotency_records (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), actor_id uuid REFERENCES app_users(id),
 route text NOT NULL, idempotency_key text NOT NULL, request_sha256 text NOT NULL,
 response_status integer NOT NULL, response_body jsonb,
 created_at timestamptz NOT NULL DEFAULT now(), expires_at timestamptz,
 UNIQUE(route,idempotency_key)
);
CREATE TABLE audit_events (
 id bigserial PRIMARY KEY, actor_user_id uuid REFERENCES app_users(id),
 actor_type text NOT NULL DEFAULT 'user', action text NOT NULL,
 subject_kind text NOT NULL, subject_id text,
 before_hash text, after_hash text, reason text, trace_id text,
 details jsonb NOT NULL DEFAULT '{}'::jsonb, created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_audit_subject ON audit_events(subject_kind,subject_id,created_at DESC);

COMMIT;

-- INITIAL MIGRATION VERIFICATION (execute as separate read-only check):
-- SELECT count(*) FROM information_schema.tables WHERE table_schema='public';
-- SELECT conname, conrelid::regclass FROM pg_constraint WHERE contype='f';
-- Check in migration tests that every FK constraint, partial unique index and enum-like state
-- is exercised. Do NOT run DDL against any existing Scrapper database.
