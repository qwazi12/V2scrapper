"""Deterministic OpenAPI contract generator for the fresh SCOS project.
Run: python generate_openapi.py; edits should be reviewed with generated 04_OPENAPI.yaml.
No network calls, no dependency on Scrapper.
"""
from pathlib import Path
import yaml

D = lambda t='string', **kw: {'type':t,**kw}
REF=lambda n: {'$ref':f'#/components/schemas/{n}'}
S=lambda **kw:D('string',**kw)
OBJ=lambda props=None,req=None,extras=False:{'type':'object','properties':props or {},'required':req or [],'additionalProperties':extras}
ARR=lambda item:{'type':'array','items':item}
ENUM=lambda vals:{'type':'string','enum':vals}
UUID=S(format='uuid')
TS=S(format='date-time')
URL=S(format='uri')
HASH=S(pattern='^[0-9a-f]{64}$')
INT=lambda **kw:D('integer',**kw)
NUM=lambda **kw:D('number',**kw)
SCO={
 'Error':OBJ({'code':S(),'message':S(),'trace_id':S(),'details':D('object',additionalProperties=True)},['code','message','trace_id'],True),
 'Page':OBJ({'next_cursor':S(nullable=True),'count':INT(),'total_estimate':INT(nullable=True)},['count'],True),
 'Session':OBJ({'user_id':UUID,'email':S(),'role':ENUM(['owner','editor','viewer']),'environment':ENUM(['local','ci','staging','production'])},['user_id','email','role','environment']),
 'Capability':OBJ({'provider':S(),'account_id':UUID,'can_upload_video':D('boolean'),'can_publish_reels':D('boolean'),'can_publish_images':D('boolean'),'can_publish_carousel':D('boolean'),'can_list_comments':D('boolean'),'can_reply':D('boolean'),'can_read_analytics':D('boolean'),'scopes':ARR(S()),'last_verified_at':TS,'last_error':S(nullable=True)},['provider','account_id']),
 'Account':OBJ({'id':UUID,'platform':ENUM(['youtube','instagram','facebook','other']),'display_name':S(),'handle':S(nullable=True),'external_account_id':S(),'publish_enabled':D('boolean'),'read_enabled':D('boolean'),'capabilities':REF('Capability')},['id','platform','display_name','external_account_id','publish_enabled']),
 'OpportunityCreate':OBJ({'title':S(minLength=3),'audience_hypothesis':S(minLength=5),'angle':S(),'payoff':S(),'why_us':S(),'evidence_urls':ARR(URL)},['title','audience_hypothesis']),
 'Opportunity':OBJ({'id':UUID,'title':S(),'audience_hypothesis':S(),'angle':S(),'payoff':S(),'why_us':S(),'status':ENUM(['new','triaged','research_pending','researching','researched','accepted','rejected','deferred']),'revision':INT(),'signals':ARR(REF('Signal')),'created_at':TS},['id','title','audience_hypothesis','status','revision']),
 'OpportunityPatch':OBJ({'angle':S(),'payoff':S(),'why_us':S(),'status':ENUM(['triaged','deferred','rejected']),'reason':S(),'expected_revision':INT()},['expected_revision']),
 'Signal':OBJ({'source_name':S(),'measurement_kind':S(),'observed_at':TS,'period_start':TS,'period_end':TS,'value':NUM(nullable=True),'units':S(),'confidence':ENUM(['observed','estimated','heuristic','opinion','unknown']),'evidence_url':URL},['source_name','measurement_kind','confidence']),
 'SourceCreate':OBJ({'provider':S(),'uri':URL,'source_kind':S(),'title':S(),'published_at':TS},['provider','uri']),
 'Source':OBJ({'id':UUID,'provider':S(),'uri':URL,'retrieved_at':TS,'published_at':TS,'content_sha256':HASH,'trust_class':S(),'title':S(),'snippet':S(),'rights_to_store':S()},['id','provider','uri','retrieved_at']),
 'ClaimCreate':OBJ({'opportunity_id':UUID,'subject_entity_id':UUID,'text':S(minLength=5),'kind':S(),'epistemic_type':ENUM(['fact','inference','opinion','rumor','unknown']),'factual_value':D('object',additionalProperties=True)},['opportunity_id','text','kind','epistemic_type']),
 'Claim':OBJ({'id':UUID,'opportunity_id':UUID,'text':S(),'kind':S(),'epistemic_type':S(),'status':ENUM(['proposed','evidence_pending','supported','contradicted','uncertain','rejected']),'revision':INT(),'evidence':ARR(REF('Evidence'))},['id','text','kind','epistemic_type','status','revision']),
 'Evidence':OBJ({'id':UUID,'claim_id':UUID,'source_id':UUID,'stance':ENUM(['supports','contradicts','mentions','unknown']),'locator':S(),'excerpt':S(),'review_method':S(),'reviewed_at':TS},['id','claim_id','source_id','stance','locator']),
 'EvidenceReview':OBJ({'source_id':UUID,'stance':ENUM(['supports','contradicts','mentions','unknown']),'locator':S(minLength=1),'excerpt':S(),'structured_field':S(),'reason':S()},['source_id','stance','locator','reason']),
 'ResearchPackageCreate':OBJ({'opportunity_id':UUID,'claim_ids':ARR(UUID),'summary':S(),'policy_version':S()},['opportunity_id','claim_ids','summary','policy_version']),
 'ResearchPackage':OBJ({'id':UUID,'opportunity_id':UUID,'revision':INT(),'claim_ids':ARR(UUID),'status':ENUM(['draft','blocked','approved','revoked']),'content_hash':HASH,'blockers':ARR(S())},['id','opportunity_id','revision','status','content_hash']),
 'Decision':OBJ({'decision':ENUM(['approve','reject','defer','revoke']),'reason':S(minLength=3),'expected_hash':HASH},['decision','reason']),
 'CampaignCreate':OBJ({'opportunity_id':UUID,'research_package_id':UUID,'title':S(),'viewer_promise':S(minLength=6),'original_angle':S(minLength=6),'series_name':S(),'spoiler_policy':S()},['research_package_id','title','viewer_promise','original_angle']),
 'Campaign':OBJ({'id':UUID,'opportunity_id':UUID,'research_package_id':UUID,'title':S(),'viewer_promise':S(),'original_angle':S(),'status':S(),'revision':INT(),'variants':ARR(REF('Variant'))},['id','research_package_id','title','viewer_promise','original_angle','status','revision']),
 'VariantCreate':OBJ({'format':ENUM(['long_16_9','short_9_16','reel_9_16','carousel_4_5','image_1_1','story_9_16','text_post']),'angle':S(minLength=5),'intended_platform':S(),'target_duration_ms':INT(minimum=1),'config':D('object',additionalProperties=True)},['format','angle']),
 'Variant':OBJ({'id':UUID,'campaign_id':UUID,'format':S(),'angle':S(),'status':S(),'target_duration_ms':INT(),'script_revision':INT()},['id','campaign_id','format','angle','status']),
 'ScriptRevision':OBJ({'revision':INT(),'text':S(),'sentences':ARR(REF('Sentence')),'text_sha256':HASH,'status':S()},['revision','text','sentences','text_sha256','status']),
 'Sentence':OBJ({'sentence_id':S(),'text':S(),'kind':ENUM(['factual','interpretation','opinion','transition','cta']),'claim_refs':ARR(UUID),'beat_index':INT(minimum=0)},['sentence_id','text','kind','claim_refs']),
 'ScriptUpdate':OBJ({'expected_revision':INT(),'sentences':ARR(REF('Sentence')),'editor_note':S()},['expected_revision','sentences']),
 'AssetCreate':OBJ({'filename':S(),'kind':S(),'byte_size':INT(minimum=0),'sha256':HASH,'mime_type':S(),'origin_type':S()},['filename','kind','byte_size','sha256','mime_type','origin_type']),
 'UploadIntent':OBJ({'asset_id':UUID,'method':ENUM(['PUT']),'upload_url':URL,'required_headers':D('object',additionalProperties={'type':'string'}),'expires_at':TS},['asset_id','method','upload_url','expires_at']),
 'AssetCommit':OBJ({'sha256':HASH,'byte_size':INT(minimum=0),'mime_type':S()},['sha256','byte_size','mime_type']),
 'Asset':OBJ({'id':UUID,'kind':S(),'filename':S(),'sha256':HASH,'status':S(),'byte_size':INT(),'rights_state':S(),'duration_ms':INT(),'width':INT(),'height':INT()},['id','kind','filename','sha256','status','byte_size','rights_state']),
 'RightsGrant':OBJ({'rights_kind':ENUM(['owner_created','licensed','provider_permitted','reference_only','pending','prohibited']),'rights_holder':S(),'proof_asset_id':UUID,'valid_to':TS,'platforms':ARR(S()),'permitted_uses':ARR(S()),'derivatives_allowed':D('boolean'),'monetization_allowed':D('boolean'),'territory':S(),'attribution':S(),'review_note':S()},['rights_kind','platforms','permitted_uses','derivatives_allowed','review_note']),
 'RenderCreate':OBJ({'variant_id':UUID,'script_revision':INT(),'brand_kit_id':UUID,'output_profile':S(),'force':D('boolean',default=False)},['variant_id','script_revision','output_profile']),
 'Job':OBJ({'id':UUID,'kind':S(),'status':S(),'stage':S(),'progress':NUM(),'attempt_count':INT(),'last_error_code':S(),'last_error_summary':S(),'created_at':TS},['id','kind','status','attempt_count','created_at']),
 'QualityCheck':OBJ({'check_name':S(),'severity':ENUM(['blocker','warning','info']),'status':ENUM(['pass','fail','inconclusive','skipped']),'observed_value':D('object',additionalProperties=True),'evidence_url':URL},['check_name','severity','status']),
 'Export':OBJ({'id':UUID,'variant_id':UUID,'sha256':HASH,'input_snapshot_hash':HASH,'format':S(),'status':S(),'size_bytes':INT(),'duration_ms':INT(),'width':INT(),'height':INT(),'qa':ARR(REF('QualityCheck'))},['id','variant_id','sha256','input_snapshot_hash','format','status']),
 'ExportApproval':OBJ({'approval_kind':ENUM(['editorial','rights','publish_ready']),'export_sha256':HASH,'input_snapshot_hash':HASH,'review_note':S(minLength=2)},['approval_kind','export_sha256','input_snapshot_hash','review_note']),
 'PlatformPackageCreate':OBJ({'export_id':UUID,'account_id':UUID,'title':S(),'caption':S(),'tags':ARR(S()),'thumbnail_asset_id':UUID,'alt_text':S(),'scheduled_at':TS},['export_id','account_id','caption']),
 'PlatformPackage':OBJ({'id':UUID,'export_id':UUID,'account_id':UUID,'title':S(),'caption':S(),'tags':ARR(S()),'status':S(),'revision':INT(),'content_hash':HASH,'validation_errors':ARR(S())},['id','export_id','account_id','status','revision','content_hash']),
 'PublicationRequest':OBJ({'package_id':UUID,'not_before':TS,'dry_run':D('boolean',default=True)},['package_id']),
 'Publication':OBJ({'id':UUID,'package_id':UUID,'state':ENUM(['draft','scheduled','claimed','submitting','provider_processing','confirmed','rejected','unknown','cancelled']),'external_post_id':S(nullable=True),'external_request_id':S(nullable=True),'last_checked_at':TS,'error_code':S(nullable=True)},['id','package_id','state']),
 'CommentThread':OBJ({'id':UUID,'account_id':UUID,'external_thread_id':S(),'external_post_id':S(),'category':S(),'status':S(),'summary':S(),'reply_count':INT()},['id','account_id','external_thread_id','status']),
 'ReplyDraftCreate':OBJ({'parent_comment_id':S(),'draft_text':S(minLength=1)},['parent_comment_id','draft_text']),
 'ReplyDraft':OBJ({'id':UUID,'thread_id':UUID,'draft_text':S(),'draft_hash':HASH,'state':S(),'external_reply_id':S(nullable=True)},['id','thread_id','draft_text','draft_hash','state']),
 'ReplyApprove':OBJ({'expected_draft_hash':HASH,'reason':S()},['expected_draft_hash']),
 'AnalyticsSync':OBJ({'start_date':S(format='date'),'end_date':S(format='date'),'dimensions':ARR(S()),'metrics':ARR(S())},['start_date','end_date']),
 'Observation':OBJ({'id':UUID,'account_id':UUID,'external_post_id':S(),'metric':S(),'value':NUM(nullable=True),'unit':S(),'period_start':TS,'period_end':TS,'observed_at':TS,'confidence':S(),'source':S(),'missing_reason':S(nullable=True)},['id','account_id','metric','unit','period_start','period_end','observed_at','confidence']),
 'ExperimentCreate':OBJ({'name':S(minLength=5),'campaign_id':UUID,'hypothesis':S(minLength=10),'primary_metric':S(),'success_criterion':S(minLength=5),'cohort_rules':D('object',additionalProperties=True),'arms':ARR(OBJ({'name':S(),'package_id':UUID,'creative_version_hash':HASH},['name','creative_version_hash']))},['name','hypothesis','primary_metric','success_criterion','cohort_rules','arms']),
 'Experiment':OBJ({'id':UUID,'name':S(),'hypothesis':S(),'state':S(),'primary_metric':S(),'pre_registered_at':TS,'conclusion':S(nullable=True)},['id','name','hypothesis','state','primary_metric']),
 'Budget':OBJ({'policy_key':S(),'period':ENUM(['daily','monthly','campaign']),'limit_amount_usd':NUM(minimum=0),'reserved_amount_usd':NUM(),'consumed_amount_usd':NUM(),'enabled':D('boolean')},['policy_key','period','limit_amount_usd','enabled']),
 'FeatureFlagChange':OBJ({'enabled':D('boolean'),'reason':S(minLength=3)},['enabled','reason']),
 'MonitorCreate':OBJ({'provider':S(),'external_id':S(),'canonical_url':URL,'subject':S(),'scope':ENUM(['metadata_only'])},['provider','external_id','canonical_url','subject','scope']),
 'DryRun':OBJ({'ready':D('boolean'),'errors':ARR(S()),'warnings':ARR(S()),'capability_verified_at':TS,'cost_estimate_usd':NUM()},['ready','errors','warnings']),
 'ArchiveRequest':OBJ({'export_id':UUID,'destination':ENUM(['drive']),'folder_id':S(),'dry_run':D('boolean',default=True)},['export_id','destination','folder_id']),
 'Archive':OBJ({'id':UUID,'export_id':UUID,'state':S(),'file_id':S(nullable=True),'last_checked_at':TS},['id','export_id','state']),
 'Status':OBJ({'status':ENUM(['ok','degraded','unavailable']),'environment':S(),'details':D('object',additionalProperties=True)},['status','environment']),
}

paths={}
def endpoint(path,method,tag,summary,req=None,resp=None,code=200,pathvars=(),query=(),idempotency=False,description=None):
    op={'tags':[tag],'summary':summary,'operationId':method+'_'+path.strip('/').replace('/','_').replace('{','').replace('}','').replace('-','_'),
        'responses':{str(code):{'description':'Successful response','content':{'application/json':{'schema':REF(resp) if resp else OBJ({},[],True)}}},
        '400':{'description':'Invalid request','content':{'application/json':{'schema':REF('Error')}}},
        '401':{'description':'Not authenticated','content':{'application/json':{'schema':REF('Error')}}},
        '403':{'description':'Not authorized or capability disabled','content':{'application/json':{'schema':REF('Error')}}},
        '409':{'description':'Conflict, stale revision or unresolved external attempt','content':{'application/json':{'schema':REF('Error')}}},
        '422':{'description':'Validation failure','content':{'application/json':{'schema':REF('Error')}}},
        '429':{'description':'Quota, budget or rate limit','content':{'application/json':{'schema':REF('Error')}}}}}
    if description:op['description']=description
    params=[]
    for name in pathvars:params.append({'name':name,'in':'path','required':True,'schema':UUID if name.endswith('_id') or name in ('id','cid','eid','job_id','oid','asset_id','thread_id','account_id','package_id') else S()})
    for name in query:params.append({'name':name,'in':'query','required':False,'schema':INT(minimum=1) if name in ('limit',) else S()})
    if idempotency:params.append({'name':'Idempotency-Key','in':'header','required':True,'schema':S(minLength=8,maxLength=128),'description':'Client-generated unique key. Same key + different payload returns 409.'})
    if method in ('post','put','patch','delete') and path not in ('/api/v1/auth/logout',):
        params.append({'name':'X-CSRF-Token','in':'header','required':True,'schema':S(),'description':'Origin-bound anti-CSRF token for browser session.'})
    if params:op['parameters']=params
    if req:op['requestBody']={'required':True,'content':{'application/json':{'schema':REF(req)}}}
    paths.setdefault(path,{})[method]=op

def E(p,m,t,s,**kw):endpoint(p,m,t,s,**kw)
# Boot/security/system
E('/health/live','get','ops','Process liveness',resp='Status')
E('/health/ready','get','ops','Readiness of API, DB and storage',resp='Status')
E('/api/v1/auth/session','get','auth','Current owner session',resp='Session')
E('/api/v1/auth/logout','post','auth','Revoke session')
E('/api/v1/control-room','get','ops','Dashboard overview and attention queue')
E('/api/v1/capabilities','get','ops','Feature and external provider capability matrix')
E('/api/v1/feature-flags','get','ops','Read feature flags')
E('/api/v1/feature-flags/{name}','patch','ops','Owner changes an environment-scoped feature flag',req='FeatureFlagChange',pathvars=('name',),resp='Status',idempotency=True)
E('/api/v1/operations/pause-publishing','post','ops','Immediately disable new external submissions',resp='Status',idempotency=True)
E('/api/v1/operations/resume-publishing','post','ops','Owner restores permitted submissions after health checks',resp='Status',idempotency=True)
E('/api/v1/events','get','ops','SSE job and domain events, cursor resume',query=('cursor',))
E('/api/v1/audit-events','get','ops','Paginated read-only audit trail',query=('cursor','limit'))
# Discovery
E('/api/v1/opportunities','get','discovery','List opportunities',query=('status','cursor','limit'))
E('/api/v1/opportunities','post','discovery','Create original idea or manual opportunity',req='OpportunityCreate',resp='Opportunity',code=201,idempotency=True)
E('/api/v1/opportunities/{id}','get','discovery','Get opportunity with evidence',resp='Opportunity',pathvars=('id',))
E('/api/v1/opportunities/{id}','patch','discovery','Revise/triage opportunity with optimistic concurrency',req='OpportunityPatch',resp='Opportunity',pathvars=('id',),idempotency=True)
E('/api/v1/opportunities/{id}/research','post','discovery','Launch bounded read/research job',resp='Job',pathvars=('id',),code=202,idempotency=True)
E('/api/v1/monitors','get','discovery','List metadata-only external source monitors')
E('/api/v1/monitors','post','discovery','Create channel/news metadata monitor, no audiovisual downloads',req='MonitorCreate',code=201,idempotency=True)
E('/api/v1/monitors/{id}/refresh','post','discovery','Discover newly available metadata',pathvars=('id',),resp='Job',code=202,idempotency=True)
# Research
E('/api/v1/sources','post','research','Register permitted source and retrieve metadata snapshot',req='SourceCreate',resp='Source',code=201,idempotency=True)
E('/api/v1/sources/{id}','get','research','Read source provenance and stored limited excerpt',resp='Source',pathvars=('id',))
E('/api/v1/claims','post','research','Create atomic claim',req='ClaimCreate',resp='Claim',code=201,idempotency=True)
E('/api/v1/claims/{id}','get','research','Read claim, verdict and evidence',resp='Claim',pathvars=('id',))
E('/api/v1/claims/{id}/evidence','post','research','Attach review of a specific evidence span',req='EvidenceReview',resp='Evidence',pathvars=('id',),code=201,idempotency=True)
E('/api/v1/claims/{id}/adjudicate','post','research','Recompute independent claim verdict',resp='Claim',pathvars=('id',),idempotency=True)
E('/api/v1/research-packages','post','research','Assemble versioned research package',req='ResearchPackageCreate',resp='ResearchPackage',code=201,idempotency=True)
E('/api/v1/research-packages/{id}','get','research','Read package and unresolved blockers',resp='ResearchPackage',pathvars=('id',))
E('/api/v1/research-packages/{id}/decision','post','research','Owner approves/rejects fixed hash of evidence package',req='Decision',resp='ResearchPackage',pathvars=('id',),idempotency=True)
# Campaigns
E('/api/v1/campaigns','get','editorial','List campaigns',query=('status','cursor','limit'))
E('/api/v1/campaigns','post','editorial','Create campaign from approved research',req='CampaignCreate',resp='Campaign',code=201,idempotency=True)
E('/api/v1/campaigns/{id}','get','editorial','Campaign including all variants',resp='Campaign',pathvars=('id',))
E('/api/v1/campaigns/{id}/variants','post','editorial','Create distinct format-specific treatment',req='VariantCreate',resp='Variant',pathvars=('id',),code=201,idempotency=True)
E('/api/v1/variants/{id}','get','editorial','Get a format-specific variant',resp='Variant',pathvars=('id',))
E('/api/v1/variants/{id}/scripts','get','editorial','List script revision history',pathvars=('id',))
E('/api/v1/variants/{id}/scripts','put','editorial','Create next script revision (immutable)',req='ScriptUpdate',resp='ScriptRevision',pathvars=('id',),idempotency=True)
E('/api/v1/variants/{id}/script/verify','post','editorial','Validate script claim refs and editorial gates',resp='DryRun',pathvars=('id',),idempotency=True)
# assets
E('/api/v1/assets','get','assets','Search permitted media assets',query=('kind','rights','q','cursor','limit'))
E('/api/v1/assets/upload-intents','post','assets','Create short-lived single-object upload intent',req='AssetCreate',resp='UploadIntent',code=201,idempotency=True)
E('/api/v1/assets/{id}/complete','post','assets','Verify uploaded bytes, hash, content and quarantine state',req='AssetCommit',resp='Asset',pathvars=('id',),idempotency=True)
E('/api/v1/assets/{id}','get','assets','Inspect asset metadata and permissions',resp='Asset',pathvars=('id',))
E('/api/v1/assets/{id}/rights','post','assets','Record reviewed rights grant, no auto-permission inference',req='RightsGrant',resp='Asset',pathvars=('id',),code=201,idempotency=True)
E('/api/v1/assets/{id}/analysis','post','assets','Schedule authorized scene/audio/transcript extraction',pathvars=('id',),resp='Job',code=202,idempotency=True)
E('/api/v1/assets/{id}/view','get','assets','Return single short-lived view URL',pathvars=('id',))
# media production
E('/api/v1/renders','post','production','Create version-pinned render request',req='RenderCreate',resp='Job',code=202,idempotency=True)
E('/api/v1/jobs','get','production','List jobs with progress and blockers',query=('status','kind','cursor','limit'))
E('/api/v1/jobs/{id}','get','production','Job stage, errors and receipts',resp='Job',pathvars=('id',))
E('/api/v1/jobs/{id}/cancel','post','production','Cooperative cancellation',pathvars=('id',),resp='Job',idempotency=True)
E('/api/v1/jobs/{id}/retry','post','production','Manually retry safe blocked/failed job after inspection',pathvars=('id',),resp='Job',idempotency=True)
E('/api/v1/exports/{id}','get','quality','Inspect immutable export + technical QA',resp='Export',pathvars=('id',))
E('/api/v1/exports/{id}/review','get','quality','Get QC report, source and rights validity',pathvars=('id',))
E('/api/v1/exports/{id}/approve','post','quality','Approve one immutable export by hash',req='ExportApproval',resp='Export',pathvars=('id',),idempotency=True)
E('/api/v1/exports/{id}/preview','get','quality','Generate short-lived signed preview URL',pathvars=('id',))
E('/api/v1/exports/{id}/revoke','post','quality','Revoke future publication eligibility',req='Decision',resp='Export',pathvars=('id',),idempotency=True)
E('/api/v1/exports/{id}/archive','post','assets','Archive approved export to owner Drive folder',req='ArchiveRequest',resp='Archive',pathvars=('id',),code=202,idempotency=True)
# accounts and publishing
E('/api/v1/social/accounts','get','distribution','Connected account status and capabilities')
E('/api/v1/social/accounts/{id}/capabilities','get','distribution','Refresh provider feature checks',resp='Capability',pathvars=('id',))
E('/api/v1/social/accounts/{id}/enable-publishing','post','distribution','Enable verified account explicitly, owner only',req='Decision',resp='Account',pathvars=('id',),idempotency=True)
E('/api/v1/social/accounts/{id}/disable-publishing','post','distribution','Disable new submissions on one account',pathvars=('id',),resp='Account',idempotency=True)
E('/api/v1/social/oauth/{provider}/start','post','distribution','Owner begins official OAuth link flow',pathvars=('provider',))
E('/api/v1/social/packages','post','distribution','Create platform-specific content package',req='PlatformPackageCreate',resp='PlatformPackage',code=201,idempotency=True)
E('/api/v1/social/packages/{id}','get','distribution','Inspect immutable version and platform details',resp='PlatformPackage',pathvars=('id',))
E('/api/v1/social/packages/{id}/validate','post','distribution','Validate media, caption, rights, platform capability',resp='DryRun',pathvars=('id',),idempotency=True)
E('/api/v1/social/packages/{id}/approve','post','distribution','Owner approve package by exact hash',req='Decision',resp='PlatformPackage',pathvars=('id',),idempotency=True)
E('/api/v1/publications','post','distribution','Create scheduled or dry-run publish intent',req='PublicationRequest',resp='Publication',code=201,idempotency=True)
E('/api/v1/publications','get','distribution','List per-platform publication records',query=('state','account_id','cursor','limit'))
E('/api/v1/publications/{id}','get','distribution','Read attempt, provider receipts and status',resp='Publication',pathvars=('id',))
E('/api/v1/publications/{id}/reconcile','post','distribution','Read-only reconcile provider result',resp='Publication',pathvars=('id',),idempotency=True)
E('/api/v1/publications/{id}/cancel','post','distribution','Cancel only before irreversible provider submission',resp='Publication',pathvars=('id',),idempotency=True)
# comments
E('/api/v1/community/threads','get','community','List categorized owner comments',query=('category','status','cursor','limit'))
E('/api/v1/community/threads/{id}','get','community','Thread and reply history',resp='CommentThread',pathvars=('id',))
E('/api/v1/community/accounts/{id}/sync','post','community','Fetch authorized comments in bounded period',resp='Job',pathvars=('id',),code=202,idempotency=True)
E('/api/v1/community/threads/{id}/reply-drafts','post','community','Create reply draft; never publish directly',req='ReplyDraftCreate',resp='ReplyDraft',pathvars=('id',),code=201,idempotency=True)
E('/api/v1/community/replies/{id}/approve','post','community','Owner approve exact reply hash',req='ReplyApprove',resp='ReplyDraft',pathvars=('id',),idempotency=True)
E('/api/v1/community/replies/{id}/send','post','community','Submit individually approved reply with reconciliation',resp='ReplyDraft',pathvars=('id',),idempotency=True)
# metrics and learning
E('/api/v1/analytics/accounts/{id}/sync','post','analytics','Request bounded authorized analytics sync',req='AnalyticsSync',resp='Job',pathvars=('id',),code=202,idempotency=True)
E('/api/v1/analytics/observations','get','analytics','Read provenance-tagged metric observations',query=('account_id','metric','from','to','cursor','limit'))
E('/api/v1/analytics/diagnostics','get','analytics','Format- and age-normalized performance diagnosis',query=('campaign_id','window'))
E('/api/v1/analytics/learning','get','analytics','Evidence-led recommendations and missing data warnings')
E('/api/v1/experiments','post','analytics','Pre-register experiment with hypothesis and metric',req='ExperimentCreate',resp='Experiment',code=201,idempotency=True)
E('/api/v1/experiments','get','analytics','List experiments',query=('state','cursor','limit'))
E('/api/v1/experiments/{id}','get','analytics','Experiment evidence, coverage and conclusion',resp='Experiment',pathvars=('id',))
# costs
E('/api/v1/budgets','get','ops','Read cost and reservations by provider')
E('/api/v1/budgets/{policy_key}','patch','ops','Owner changes cost limit',req='Budget',pathvars=('policy_key',),resp='Budget',idempotency=True)

# Completion schemas and structured list/report responses; no untyped success payloads.
SCO.update({
 'StatusDetail':OBJ({'ok':D('boolean'),'message':S(),'environment':S(),'changed':D('boolean')},['ok','message'],True),
 'FeatureFlag':OBJ({'name':S(),'environment':S(),'enabled':D('boolean'),'reason':S(),'updated_at':TS},['name','environment','enabled']),
 'AttentionItem':OBJ({'id':UUID,'kind':S(),'severity':S(),'subject_kind':S(),'subject_id':UUID,'reason':S(),'suggested_action':S()},['id','kind','severity','reason']),
 'ControlRoom':OBJ({'attention':ARR(REF('AttentionItem')),'recommended_opportunity_ids':ARR(UUID),'active_jobs':ARR(REF('Job')),'publishing_disabled':D('boolean'),'provider_health':ARR(REF('Capability')),'budgets':ARR(REF('Budget'))},['attention','recommended_opportunity_ids','active_jobs','publishing_disabled']),
 'OAuthLink':OBJ({'authorization_url':URL,'state_expires_at':TS,'provider':S()},['authorization_url','state_expires_at','provider']),
 'SignedObject':OBJ({'object_id':UUID,'url':URL,'expires_at':TS,'method':S()},['object_id','url','expires_at']),
 'ReviewReport':OBJ({'export':REF('Export'),'checks':ARR(REF('QualityCheck')),'blocking_reasons':ARR(S()),'owner_approval_required':D('boolean'),'rights_snapshot_hash':HASH},['export','checks','blocking_reasons','owner_approval_required']),
 'Diagnostics':OBJ({'platform':S(),'format':S(),'cohort_rule':S(),'sample_size':INT(),'data_coverage':S(),'observations':ARR(REF('Observation')),'findings':ARR(S()),'counterevidence':ARR(S()),'conclusion':S(),'confidence':S()},['cohort_rule','sample_size','data_coverage','findings','confidence']),
 'Learning':OBJ({'recommendations':ARR(OBJ({'text':S(),'hypothesis':S(),'observation_ids':ARR(UUID),'next_test':S(),'kill_criterion':S(),'confidence':S()},['text','hypothesis','observation_ids','next_test','confidence'])),'gaps':ARR(S()),'as_of':TS},['recommendations','gaps','as_of']),
 'BudgetUpdate':OBJ({'limit_amount_usd':NUM(minimum=0),'enabled':D('boolean'),'reason':S(minLength=3)},['limit_amount_usd','enabled','reason']),
 'PublishingResume':OBJ({'typed_confirmation':ENUM(['ENABLE_SCOS_PUBLISHING']),'reason':S(minLength=3)},['typed_confirmation','reason']),
 'OwnerApproval':OBJ({'expected_hash':HASH,'review_note':S(minLength=3)},['expected_hash','review_note']),
 'Storyboard':OBJ({'variant_id':UUID,'revision':INT(),'script_sha256':HASH,'beats':ARR(OBJ({'start_ms':INT(minimum=0),'end_ms':INT(minimum=1),'asset_id':UUID,'script_sentence_ids':ARR(S()),'caption_ids':ARR(S()),'transition':S()},['start_ms','end_ms','script_sentence_ids'])),'content_hash':HASH},['variant_id','revision','script_sha256','beats','content_hash']),
 'StoryboardUpdate':OBJ({'expected_revision':INT(),'beats':ARR(OBJ({'start_ms':INT(minimum=0),'end_ms':INT(minimum=1),'asset_id':UUID,'script_sentence_ids':ARR(S()),'caption_ids':ARR(S()),'transition':S()},['start_ms','end_ms','script_sentence_ids']))},['expected_revision','beats']),
 'AnalyticsImport':OBJ({'account_id':UUID,'source_kind':ENUM(['authorized_csv','manual_owner_export']),'source_asset_id':UUID,'metric_definition_version':S(),'confirm_owner_source':D('boolean')},['account_id','source_kind','source_asset_id','metric_definition_version','confirm_owner_source']),
 'AccountEnable':OBJ({'external_account_id':S(),'expected_capability_hash':HASH,'typed_confirmation':ENUM(['ENABLE_PUBLISHING_FOR_THIS_ACCOUNT']),'reason':S(minLength=3)},['external_account_id','expected_capability_hash','typed_confirmation','reason']),
 'Monitor':OBJ({'id':UUID,'provider':S(),'external_id':S(),'canonical_url':URL,'subject':S(),'scope':S(),'enabled':D('boolean'),'last_checked_at':TS},['id','provider','external_id','canonical_url','subject','scope','enabled']),
 'AuditEvent':OBJ({'id':INT(),'actor_user_id':UUID,'actor_type':S(),'action':S(),'subject_kind':S(),'subject_id':S(),'created_at':TS,'trace_id':S()},['id','actor_type','action','subject_kind','created_at']),
 'CostEvent':OBJ({'id':UUID,'job_id':UUID,'provider':S(),'operation':S(),'amount_usd':NUM(nullable=True),'observed_at':TS},['id','provider','operation','observed_at']),
 'ScriptRevisionSummary':OBJ({'id':UUID,'revision':INT(),'text_sha256':HASH,'review_status':S(),'created_at':TS},['id','revision','text_sha256','review_status']),
 'CapabilityMatrixSummary':OBJ({'environment':S(),'providers':ARR(REF('Capability')),'flags':ARR(REF('FeatureFlag')),'external_writes_disabled':D('boolean')},['environment','providers','flags','external_writes_disabled']),
 'CommentImportStatus':OBJ({'account_id':UUID,'job_id':UUID,'estimated_page_count':INT()},['account_id','job_id']),
 'ExportList':OBJ({'items':ARR(REF('Export')),'page':REF('Page')},['items','page']),
})
for typ,sing in [('Opportunity','Opportunity'),('Source','Source'),('Claim','Claim'),('Campaign','Campaign'),('Asset','Asset'),('Job','Job'),('Publication','Publication'),('CommentThread','CommentThread'),('Account','Account'),('PlatformPackage','PlatformPackage'),('Observation','Observation'),('Experiment','Experiment'),('Budget','Budget'),('FeatureFlag','FeatureFlag'),('Monitor','Monitor'),('AuditEvent','AuditEvent'),('CostEvent','CostEvent'),('ScriptRevisionSummary','ScriptRevisionSummary')]:
 SCO[typ+'List']=OBJ({'items':ARR(REF(sing)),'page':REF('Page')},['items','page'])

# Explicit lists + owner login (OIDC callback has verified state, no owner session yet).
E('/api/v1/auth/oidc/start','get','auth','Begin separate SCOS owner identity provider login',resp='OAuthLink')
E('/api/v1/auth/oidc/callback','get','auth','Verify state and exchange OIDC authorization code, then redirect',query=('state','code'))
E('/api/v1/social/oauth/{provider}/callback','get','distribution','Verify platform OAuth state, link grant, and redirect',pathvars=('provider',),query=('state','code'))
E('/api/v1/sources','get','research','List stored permitted source records',query=('cursor','limit'),resp='SourceList')
E('/api/v1/claims','get','research','List claims by opportunity and state',query=('opportunity_id','status','cursor','limit'),resp='ClaimList')
E('/api/v1/variants/{id}/storyboard','get','editorial','Read versioned storyboard for variant',pathvars=('id',),resp='Storyboard')
E('/api/v1/variants/{id}/storyboard','put','editorial','Create storyboard revision',req='StoryboardUpdate',pathvars=('id',),resp='Storyboard',idempotency=True)
E('/api/v1/campaigns/{id}/approve-brief','post','editorial','Owner approves brief and approved source hash',req='OwnerApproval',pathvars=('id',),resp='Campaign',idempotency=True)
E('/api/v1/variants/{id}/approve-script','post','editorial','Owner approves verified script revision',req='OwnerApproval',pathvars=('id',),resp='ScriptRevision',idempotency=True)
E('/api/v1/exports','get','quality','List immutable media exports ready/blocked for review',query=('status','cursor','limit'),resp='ExportList')
E('/api/v1/discover/recommendations','get','discovery','Evidence-led recommended topics and counterevidence')
E('/api/v1/social/calendar','get','distribution','Owner local-time social schedule and platform statuses',query=('from','to','account_id'))
E('/api/v1/analytics/imports','post','analytics','Import owner-provided analytics export with source definition',req='AnalyticsImport',resp='Job',code=202,idempotency=True)
E('/api/v1/cost-events','get','ops','Read paid usage receipts and estimate/actual discrepancies',query=('provider','from','to','cursor','limit'))
E('/api/v1/archives/{id}','get','assets','Inspect Drive archive intent and verification state',pathvars=('id',),resp='Archive')

# Tighten endpoint response schemas on original routes.
known={
 ('/api/v1/auth/logout','post'):'StatusDetail',
 ('/api/v1/monitors','post'):'Monitor',
 ('/api/v1/control-room','get'):'ControlRoom',
 ('/api/v1/capabilities','get'):'CapabilityMatrixSummary',
 ('/api/v1/feature-flags','get'):'FeatureFlagList',
 ('/api/v1/feature-flags/{name}','patch'):'FeatureFlag',
 ('/api/v1/operations/pause-publishing','post'):'StatusDetail',
 ('/api/v1/operations/resume-publishing','post'):'StatusDetail',
 ('/api/v1/audit-events','get'):'AuditEventList',
 ('/api/v1/opportunities','get'):'OpportunityList',
 ('/api/v1/monitors','get'):'MonitorList',
 ('/api/v1/sources','get'):'SourceList',
 ('/api/v1/claims','get'):'ClaimList',
 ('/api/v1/campaigns','get'):'CampaignList',
 ('/api/v1/variants/{id}/scripts','get'):'ScriptRevisionSummaryList',
 ('/api/v1/assets','get'):'AssetList',
 ('/api/v1/assets/{id}/view','get'):'SignedObject',
 ('/api/v1/jobs','get'):'JobList',
 ('/api/v1/exports/{id}/review','get'):'ReviewReport',
 ('/api/v1/exports/{id}/preview','get'):'SignedObject',
 ('/api/v1/social/accounts','get'):'AccountList',
 ('/api/v1/social/oauth/{provider}/start','post'):'OAuthLink',
 ('/api/v1/publications','get'):'PublicationList',
 ('/api/v1/community/threads','get'):'CommentThreadList',
 ('/api/v1/analytics/observations','get'):'ObservationList',
 ('/api/v1/analytics/diagnostics','get'):'Diagnostics',
 ('/api/v1/analytics/learning','get'):'Learning',
 ('/api/v1/experiments','get'):'ExperimentList',
 ('/api/v1/budgets','get'):'BudgetList',
 ('/api/v1/budgets/{policy_key}','patch'):'Budget',
 ('/api/v1/discover/recommendations','get'):'OpportunityList',
 ('/api/v1/social/calendar','get'):'PublicationList',
 ('/api/v1/cost-events','get'):'CostEventList',
}
for (p,m),s in known.items():
 o=paths[p][m];o['responses'][next(k for k in o['responses'] if k in ('200','201','202'))]['content']['application/json']['schema']=REF(s)
paths['/api/v1/operations/resume-publishing']['post']['requestBody']={'required':True,'content':{'application/json':{'schema':REF('PublishingResume')}}}
paths['/api/v1/budgets/{policy_key}']['patch']['requestBody']['content']['application/json']['schema']=REF('BudgetUpdate')
paths['/api/v1/social/accounts/{id}/enable-publishing']['post']['requestBody']['content']['application/json']['schema']=REF('AccountEnable')
paths['/api/v1/events']['get']['responses']['200']['content']={'text/event-stream':{'schema':S(description='SSE domain event JSON framed as event/id/data')}}
for name in ('/api/v1/auth/oidc/start','/api/v1/auth/oidc/callback','/api/v1/social/oauth/{provider}/callback'):
 paths[name]['get']['security']=[]
for name in ('/api/v1/auth/oidc/callback','/api/v1/social/oauth/{provider}/callback'):
 paths[name]['get']['responses'].pop('200',None)
 paths[name]['get']['responses']['302']={'description':'Redirect to authenticated application or state-verification error','headers':{'Location':{'schema':URL}}}

# Global auth except health and external OAuth callback; callback is handled by server OIDC flow
for path,ms in paths.items():
    for method,op in ms.items():
        if not (path.startswith('/health/') or path in ('/api/v1/auth/oidc/start','/api/v1/auth/oidc/callback','/api/v1/social/oauth/{provider}/callback')):
            op['security']=[{'ownerSession':[]}] 
        if method in ('post','put','patch','delete') and 'responses' in op:
            op['responses']['503']={'description':'Dependency unavailable or provider capability disabled','content':{'application/json':{'schema':REF('Error')}}}

spec={'openapi':'3.1.0','info':{'title':'Screen Central OS Private API','version':'1.0.0','description':'Greenfield, owner-only API contract. Not backward compatible with Scrapper. Platform writes disabled by default. All POST/PATCH/PUT require Origin+CSRF and Idempotency-Key for create/side-effecting operations.'},
 'servers':[{'url':'http://localhost:8000','description':'Local mocked instance'}],
 'tags':[{'name':n} for n in ['auth','ops','discovery','research','editorial','assets','production','quality','distribution','community','analytics']],
 'paths':paths,
 'components':{'securitySchemes':{'ownerSession':{'type':'apiKey','in':'cookie','name':'__Host-scos_session','description':'HttpOnly Secure SameSite=Lax cookie; server session store. Cross-site mutation blocked via Origin and X-CSRF-Token.'}},'schemas':SCO}}

def normalize_nullable(x):
    if isinstance(x, dict):
        if x.pop('nullable',False) and isinstance(x.get('type'),str): x['type']=[x['type'],'null']
        for v in x.values():normalize_nullable(v)
    elif isinstance(x,list):
        for v in x:normalize_nullable(v)
normalize_nullable(spec)

p=Path(__file__).with_name('04_OPENAPI.yaml')
p.write_text(yaml.safe_dump(spec,sort_keys=False,width=110,allow_unicode=True))
print(p, len(paths),'paths',sum(len(x) for x in paths.values()),'methods',len(SCO),'schemas')
