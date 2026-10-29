import asyncio
from difflib import SequenceMatcher
import hashlib
import json
import os
import re
import secrets
from contextlib import asynccontextmanager
from typing import Any
from uuid import UUID
from fastapi import FastAPI, Request, Response, Depends, Query, UploadFile, File
from fastapi.responses import JSONResponse, StreamingResponse, RedirectResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, ConfigDict, Field
from psycopg import errors as pg_errors
from .config import ENV, OWNER_ID, ORIGINS, validate
from . import config, identity
from .db import connect, one, all_rows, clean, now, uid, audit
from .policy import PolicyError, require, claim_errors
from .commands import execute
from .seed import bootstrap
from . import storage


@asynccontextmanager
async def lifespan(app):
    validate()
    storage.init()
    with connect() as c:
        bootstrap(c)
    yield


app = FastAPI(title="Screen Central OS · Local implementation API", version="0.1.0", lifespan=lifespan)


def db():
    with connect() as c:
        yield c


def hash_token(value):
    return hashlib.sha256(value.encode()).digest()


def origin(request):
    require(
        request.headers.get("origin") in ORIGINS, "CSRF_MISMATCH", "Request Origin must match the local dashboard", 403
    )


def owner(request: Request, c=Depends(db)):
    token = request.cookies.get(config.SESSION_COOKIE, "")
    session = one(
        c,
        """SELECT s.*,u.display_name,u.email FROM sessions s JOIN app_users u ON u.id=s.user_id
        WHERE s.token_hash=%s AND s.expires_at>now() AND s.revoked_at IS NULL AND u.active=true""",
        (hash_token(token),),
    )
    require(session, "UNAUTHENTICATED", "Sign in to the owner workspace", 401)
    if request.method not in ("GET", "HEAD", "OPTIONS"):
        origin(request)
        supplied = request.headers.get("x-csrf-token", "")
        require(
            secrets.compare_digest(hash_token(supplied), bytes(session["csrf_hash"])),
            "CSRF_MISMATCH",
            "CSRF token is missing or invalid",
            403,
        )
    return session


@app.exception_handler(PolicyError)
async def policy_error(request, exc):
    return JSONResponse(
        {"code": exc.code, "message": exc.message, "trace_id": uid(), "details": {}}, status_code=exc.status
    )


@app.exception_handler(RequestValidationError)
async def validation_error(request, exc):
    return JSONResponse(
        {
            "code": "INVALID_INPUT",
            "message": "The request contains invalid fields",
            "details": {"fields": [str(e["loc"]) for e in exc.errors()]},
            "trace_id": uid(),
        },
        status_code=422,
    )


@app.exception_handler(pg_errors.UniqueViolation)
async def conflict(request, exc):
    return JSONResponse(
        {
            "code": "CONFLICT_REVISION",
            "message": "A matching durable record already exists. Reload to inspect it.",
            "trace_id": uid(),
            "details": {},
        },
        status_code=409,
    )


@app.get("/health/live")
def live():
    return {"status": "ok", "environment": ENV}


@app.get("/health/ready")
def ready(c=Depends(db)):
    one(c, "SELECT 1")
    storage.client().head_bucket(Bucket=storage.BUCKET)
    return {
        "status": "ok",
        "environment": ENV,
        "details": {
            "database": "postgresql",
            "storage": "private Supabase Storage"
            if config.DATA_PROVIDER == "supabase"
            else "durable private S3"
            if config.HOSTED
            else "private S3 emulator",
            "data_provider": config.DATA_PROVIDER,
            "auth_configured": config.auth_configured() if config.HOSTED else True,
            "live_publish": False,
        },
    }


@app.post("/api/v1/auth/local")
def login(request: Request, response: Response, c=Depends(db)):
    origin(request)
    require(ENV == "local", "FORBIDDEN", "Local identity is disabled outside local development", 403)
    csrf = identity.issue_session(c, response, OWNER_ID, "local_fixture")
    return {"csrf_token": csrf, "user": {"display_name": "Screen Central", "role": "owner"}, "environment": ENV}


@app.get("/api/v1/auth/session")
def session(request: Request, s=Depends(owner)):
    csrf = hashlib.sha256(("csrf:" + request.cookies[config.SESSION_COOKIE]).encode()).hexdigest()
    return {
        "csrf_token": csrf,
        "user": {"id": str(s["user_id"]), "display_name": s["display_name"], "role": "owner"},
        "environment": ENV,
    }


@app.post("/api/v1/auth/logout")
def logout(response: Response, s=Depends(owner), c=Depends(db)):
    c.execute("UPDATE sessions SET revoked_at=now() WHERE id=%s", (s["id"],))
    response.delete_cookie(
        config.SESSION_COOKIE, secure=config.HOSTED, httponly=True, samesite="lax" if config.HOSTED else "strict"
    )
    return {"ok": True}


class Command(BaseModel):
    model_config = ConfigDict(extra="forbid")
    target: UUID | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


@app.post("/api/v1/actions/{action}")
def action(action: str, body: Command, request: Request, s=Depends(owner), c=Depends(db)):
    return execute(c, action, body.target, body.payload, str(s["user_id"]), request.headers.get("idempotency-key"))


TABLES = {
    "opportunities": "opportunities",
    "campaigns": "campaigns",
    "assets": "media_assets",
    "jobs": "jobs",
    "exports": "exports",
    "publications": "publication_attempts",
    "social/accounts": "social_accounts",
    "social/packages": "platform_packages",
    "sources": "source_records",
    "claims": "claims",
    "community/threads": "comment_threads",
    "analytics/observations": "analytics_observations",
    "experiments": "experiments",
    "budgets": "budget_policies",
    "audit-events": "audit_events",
    "cost-events": "cost_events",
}


@app.get("/api/v1/workspace")
def workspace(s=Depends(owner), c=Depends(db)):
    result = {}
    for name, table in TABLES.items():
        order = {
            "analytics_observations": "observed_at",
            "experiments": "pre_registered_at",
            "social_accounts": "connected_at",
            "cost_events": "observed_at",
            "source_records": "retrieved_at",
            "budget_policies": "updated_at",
            "comment_threads": "first_seen_at",
        }.get(table, "created_at")
        result[name] = clean(all_rows(c, f"SELECT * FROM {table} ORDER BY {order} DESC LIMIT 100"))
    result["variants"] = clean(all_rows(c, "SELECT * FROM campaign_variants ORDER BY created_at"))
    result["scripts"] = clean(
        all_rows(c, "SELECT DISTINCT ON (variant_id) * FROM scripts ORDER BY variant_id,revision DESC")
    )
    result["asset_usage"] = clean(all_rows(c, "SELECT * FROM asset_usage"))
    result["rights"] = clean(all_rows(c, "SELECT * FROM asset_rights"))
    result["evidence"] = clean(
        all_rows(
            c,
            """SELECT e.*,s.uri,s.title AS source_title,s.snippet,s.retrieved_at,s.expires_at,
            s.content_sha256 AS source_content_hash,s.fetch_status AS source_status FROM claim_evidence e
        JOIN source_records s ON e.source_id=s.id""",
        )
    )
    result["approvals"] = clean(all_rows(c, "SELECT * FROM export_approvals ORDER BY approved_at DESC"))
    result["quality"] = clean(all_rows(c, "SELECT * FROM quality_checks ORDER BY executed_at DESC"))
    result["replies"] = clean(all_rows(c, "SELECT * FROM reply_drafts ORDER BY created_at DESC"))
    result["research_packages"] = clean(all_rows(c, "SELECT * FROM research_packages"))
    result["environment"] = ENV
    result["publishing_disabled"] = True
    result["data_provider"] = config.DATA_PROVIDER
    result["ai_provider"] = os.getenv("SCOS_AI_PROVIDER", "fixture")
    from . import gemini

    result["ai"] = gemini.readiness()
    result["paid_calls_disabled"] = not result["ai"]["ready"]
    result["ai_drafts"] = clean(all_rows(c, "SELECT * FROM ai_draft_calls ORDER BY created_at DESC LIMIT 100"))
    result["claim_blockers"] = {str(cl["id"]): claim_errors(c, cl["id"]) for cl in all_rows(c, "SELECT * FROM claims")}
    return result


@app.get("/api/v1/variants/{id}/scripts/history")
def script_history(id: UUID, s=Depends(owner), c=Depends(db)):
    require(one(c, "SELECT id FROM campaign_variants WHERE id=%s", (id,)), "NOT_FOUND", "Variant not found", 404)
    versions = clean(
        all_rows(
            c,
            "SELECT revision,text,sentences,text_sha256,review_status,created_at FROM scripts WHERE variant_id=%s ORDER BY revision DESC LIMIT 50",
            (id,),
        )
    )
    for index, version in enumerate(versions):
        version["changes"] = []
        if index + 1 < len(versions):
            old = [s["text"] for s in versions[index + 1]["sentences"]]
            new = [s["text"] for s in version["sentences"]]
            for tag, a, b, x, y in SequenceMatcher(a=old, b=new).get_opcodes():
                if tag in ("delete", "replace"):
                    version["changes"] += [{"kind": "removed", "text": text} for text in old[a:b]]
                if tag in ("insert", "replace"):
                    version["changes"] += [{"kind": "added", "text": text} for text in new[x:y]]
    return {"items": versions}


def list_endpoint(table):
    def endpoint(
        page: int = Query(1, ge=1), limit: int = Query(25, ge=1, le=100), q: str = "", s=Depends(owner), c=Depends(db)
    ):
        # Table names come exclusively from the constant map, not from request input.
        rows = all_rows(c, f"SELECT * FROM {table} ORDER BY id LIMIT %s OFFSET %s", (limit, (page - 1) * limit))
        total = one(c, f"SELECT count(*) AS n FROM {table}")["n"]
        return {"items": clean(rows), "page": {"number": page, "size": limit, "total": total}}

    return endpoint


for path, table in TABLES.items():
    app.add_api_route("/api/v1/" + path, list_endpoint(table), methods=["GET"], name=path.replace("/", "_") + "_list")


@app.get("/api/v1/exports/{id}/review")
def review(id: UUID, s=Depends(owner), c=Depends(db)):
    ex = one(c, "SELECT * FROM exports WHERE id=%s", (id,))
    require(ex, "NOT_FOUND", "Export not found", 404)
    checks = all_rows(c, "SELECT * FROM quality_checks WHERE export_id=%s", (id,))
    return clean(
        {
            "export": ex,
            "checks": checks,
            "blocking_reasons": [
                q["check_name"] for q in checks if q["severity"] == "blocker" and q["status"] != "pass"
            ],
            "owner_approval_required": ex["status"] != "approved",
        }
    )


@app.get("/api/v1/exports/{id}/preview")
def preview(
    id: UUID,
    request: Request,
    artifact: str = "media",
    slide: int = Query(0, ge=0, le=9),
    s=Depends(owner),
    c=Depends(db),
):
    ex = one(c, "SELECT * FROM exports WHERE id=%s", (id,))
    require(ex, "NOT_FOUND", "Export not found", 404)
    require(artifact in ("media", "poster", "slide"), "NOT_FOUND", "Unknown artifact", 404)
    key, digest = ex["object_key"], ex["sha256"]
    mime = "video/mp4" if ex["format"] in ("long_16_9", "short_9_16", "reel_9_16") else "application/zip"
    if artifact == "poster":
        key = ex["codec"]["poster_key"]
        digest = None
        mime = "image/png"
    if artifact == "slide":
        slides = ex["codec"].get("slides", [])
        require(slide < len(slides), "NOT_FOUND", "Slide not found", 404)
        key, digest = slides[slide]["key"], slides[slide]["sha256"]
        mime = "image/png"
    try:
        data = storage.read(key, digest)
    except ValueError:
        raise PolicyError("ASSET_MISMATCH", "Media checksum failed; export is not safe to approve")
    headers = {"Cache-Control": "private, no-store", "Accept-Ranges": "bytes", "X-Content-Type-Options": "nosniff"}
    range_header = request.headers.get("range", "")
    if range_header and mime == "video/mp4":
        match = re.fullmatch(r"bytes=(\d+)-(\d*)", range_header)
        require(match, "INVALID_INPUT", "Only a single byte range is supported", 416)
        start = int(match[1])
        end = int(match[2]) if match[2] else len(data) - 1
        end = min(end, len(data) - 1)
        require(start <= end and start < len(data), "INVALID_INPUT", "Range out of bounds", 416)
        headers["Content-Range"] = f"bytes {start}-{end}/{len(data)}"
        return Response(data[start : end + 1], status_code=206, media_type=mime, headers=headers)
    if mime == "application/zip":
        headers["Content-Disposition"] = f'attachment; filename="scos-{id}.zip"'
    return Response(data, media_type=mime, headers=headers)


@app.get("/api/v1/assets/{id}/view")
def asset_view(id: UUID, s=Depends(owner), c=Depends(db)):
    row = one(c, "SELECT * FROM media_assets WHERE id=%s", (id,))
    require(row and row["status"] in ("approved", "quarantine"), "NOT_FOUND", "Approved asset not found", 404)
    return Response(
        storage.read(row["object_key"], row["sha256"]),
        media_type=row["media_type"],
        headers={"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"},
    )


@app.get("/api/v1/control-room")
def control(s=Depends(owner), c=Depends(db)):
    return {
        "publishing_disabled": True,
        "environment": ENV,
        "attention": clean(
            all_rows(
                c,
                "SELECT id,'publication' AS kind,'Unknown mock outcome. Reconcile before retry.' AS reason FROM publication_attempts WHERE state='unknown'",
            )
        ),
        "active_jobs": clean(all_rows(c, "SELECT * FROM jobs WHERE status IN ('queued','running','blocked','failed')")),
        "recommended_opportunity_ids": [
            str(r["id"])
            for r in all_rows(c, "SELECT id FROM opportunities WHERE status NOT IN ('rejected','deferred')")
        ],
        "budgets": clean(all_rows(c, "SELECT * FROM budget_policies")),
    }


@app.get("/api/v1/analytics/learning")
def learning(s=Depends(owner), c=Depends(db)):
    observations = all_rows(c, "SELECT * FROM analytics_observations WHERE source='synthetic_fixture'")
    return {
        "recommendations": []
        if not observations
        else [
            {
                "text": "Test a clearer visual promise in the opening frame.",
                "hypothesis": "An immediate visual promise may improve early attention.",
                "observation_ids": [str(o["id"]) for o in observations],
                "next_test": "Pre-register two original opening treatments; compare the same format at 48 hours.",
                "kill_criterion": "Stop if factual clarity drops or comparable mature samples show no improvement.",
                "confidence": "inconclusive — synthetic sample only; no causal or real-channel inference",
            }
        ],
        "gaps": [
            "No authenticated channel observations",
            "Retention unavailable",
            "Insufficient mature comparable samples",
        ],
        "as_of": now().isoformat(),
    }


@app.get("/api/v1/capabilities")
def capabilities(s=Depends(owner)):
    return {
        "environment": ENV,
        "external_writes_disabled": True,
        "providers": [
            {"provider": p, "state": "requires_connection", "mode": "mock"}
            for p in ("youtube", "instagram", "facebook", "drive", "ai")
        ],
    }


@app.get("/api/v1/events")
async def events(s=Depends(owner)):
    async def stream():
        for _ in range(30):
            with connect() as c:
                jobs = clean(
                    all_rows(c, "SELECT id,status,output,last_error_code FROM jobs ORDER BY created_at DESC LIMIT 20")
                )
            yield "event: jobs\ndata: " + json.dumps(jobs) + "\n\n"
            await asyncio.sleep(2)

    return StreamingResponse(stream(), media_type="text/event-stream", headers={"Cache-Control": "no-cache"})


@app.post("/api/v1/assets/upload")
def upload_asset(request: Request, file: UploadFile = File(...), s=Depends(owner), c=Depends(db)):
    from io import BytesIO
    from pathlib import Path
    from PIL import Image, UnidentifiedImageError
    from .db import insert
    from .config import RUNTIME

    require(request.headers.get("idempotency-key"), "INVALID_INPUT", "Idempotency-Key required", 422)
    data = file.file.read(8 * 1024 * 1024 + 1)
    require(0 < len(data) <= 8 * 1024 * 1024, "INVALID_INPUT", "This image upload accepts up to 8 MB", 413)
    try:
        im = Image.open(BytesIO(data))
        require(
            im.format in ("PNG", "JPEG", "WEBP") and im.width * im.height <= 20000000,
            "INVALID_INPUT",
            "Use a PNG, JPEG or WebP image under 20 megapixels",
            422,
        )
        im.verify()
        im = Image.open(BytesIO(data))
        suffix = {"PNG": ".png", "JPEG": ".jpg", "WEBP": ".webp"}[im.format]
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
        raise PolicyError("INVALID_INPUT", "The image cannot be decoded; upload rejected", 422)
    digest = hashlib.sha256(data).hexdigest()
    prior = one(c, "SELECT * FROM media_assets WHERE sha256=%s AND kind='image'", (digest,))
    if prior:
        return clean(prior)
    path = RUNTIME / ("upload-" + uid() + suffix)
    path.write_bytes(data)
    key, digest, size = storage.put(path)
    path.unlink()
    filename = Path((file.filename or "image").replace("\\", "/")).name[:160]
    row = insert(
        c,
        "media_assets",
        kind="image",
        origin_type="owner_upload",
        filename=filename,
        media_type=Image.MIME[im.format],
        sha256=digest,
        byte_size=size,
        object_key=key,
        width=im.width,
        height=im.height,
        status="quarantine",
        metadata={"decode_verified": True, "rights_review_required": True},
    )
    audit(c, "asset.uploaded", row["id"], str(s["user_id"]), details={"byte_size": size, "rights_state": "pending"})
    return clean(row)


@app.get("/api/v1/auth/config")
def auth_config():
    from . import gemini

    return {
        "environment": ENV,
        "local_login_allowed": ENV == "local",
        "oidc_configured": config.auth_configured(),
        "publishing_disabled": True,
        "paid_calls_disabled": not gemini.readiness()["ready"],
    }


@app.get("/api/v1/auth/oidc/start")
def oidc_start(response: Response, c=Depends(db)):
    return identity.start_login(c, response)


@app.get("/api/v1/auth/oidc/callback")
def oidc_callback(request: Request, code: str = "", state: str = ""):
    require(config.DATA_PROVIDER != "supabase", "FORBIDDEN", "Use the configured owner sign-in provider", 403)
    require(config.auth_configured(), "AUTH_NOT_CONFIGURED", "Owner sign-in is not configured", 503)
    require(
        code and state and len(code) <= 4096 and len(state) <= 256,
        "AUTH_STATE_INVALID",
        "Google sign-in was cancelled or invalid",
        403,
    )
    login_state = identity.consume_state(state, request.cookies.get(identity.LOGIN_COOKIE, ""))
    claims = identity.exchange_code(code, login_state)
    response = RedirectResponse(config.PUBLIC_URL + "/", status_code=303)
    response.delete_cookie(identity.LOGIN_COOKIE, secure=True, httponly=True, samesite="lax")
    with connect() as c:
        user = identity.owner_from_identity(c, claims)
        identity.issue_session(c, response, user["id"])
    return response


@app.get("/api/v1/auth/supabase/callback")
def supabase_callback(request: Request, code: str = ""):
    from . import supabase_auth

    require(
        config.DATA_PROVIDER == "supabase" and config.auth_configured(),
        "AUTH_NOT_CONFIGURED",
        "Owner sign-in is not configured",
        503,
    )
    cookie = request.cookies.get(supabase_auth.LOGIN_COOKIE, "")
    require(
        code and len(code) <= 4096 and len(cookie) <= 256 and cookie.count(".") == 1,
        "AUTH_STATE_INVALID",
        "Google sign-in was cancelled, expired or opened in a different browser",
        403,
    )
    state, browser = cookie.split(".")
    login_state = identity.consume_state(state, browser)
    claims = supabase_auth.exchange_code(code, login_state)
    response = RedirectResponse(config.PUBLIC_URL + "/", status_code=303)
    response.delete_cookie(supabase_auth.LOGIN_COOKIE, secure=True, httponly=True, samesite="lax")
    with connect() as c:
        user = identity.owner_from_identity(c, claims, issuer=config.SUPABASE_URL + "/auth/v1")
        identity.issue_session(c, response, user["id"], lifetime_seconds=3600)
    return response


class AIDraftRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_input_hash: str = Field(pattern=r"^[a-f0-9]{64}$")


@app.get("/api/v1/variants/{id}/ai/quote")
def ai_quote(id: UUID, s=Depends(owner), c=Depends(db)):
    from . import gemini

    snapshot = gemini.context(c, id)
    p = gemini.price()
    return {
        "input_sha256": gemini.sha(snapshot),
        "maximum_cost_usd": str(gemini.estimate(gemini.body_for(snapshot), p)),
        "readiness": gemini.readiness(),
        "approval_required": True,
    }


@app.post("/api/v1/variants/{id}/ai/draft")
def ai_draft(id: UUID, body: AIDraftRequest, request: Request, s=Depends(owner)):
    from . import gemini

    return gemini.generate(id, s["user_id"], request.headers.get("idempotency-key"), body.expected_input_hash)


@app.post("/api/v1/ai/drafts/{id}/apply")
def ai_apply(id: UUID, request: Request, s=Depends(owner), c=Depends(db)):
    from . import gemini

    draft = one(c, "SELECT * FROM ai_draft_calls WHERE id=%s FOR UPDATE", (id,))
    require(draft and str(draft["actor_id"]) == str(s["user_id"]), "NOT_FOUND", "Draft not found", 404)
    if draft["status"] == "applied":
        return {"status": "already_applied"}
    require(draft["status"] == "succeeded", "AI_OUTPUT_INVALID", "Only a completed draft can be applied")
    snapshot = gemini.context(c, draft["variant_id"])
    require(
        gemini.sha(snapshot) == draft["input_sha256"],
        "CONFLICT_REVISION",
        "Research or script inputs changed; this draft is stale",
    )
    sentences = [{**line, "sentence_id": "s" + str(i + 1)} for i, line in enumerate(draft["output"]["sentences"])]
    result = execute(
        c,
        "script.save",
        draft["variant_id"],
        {"expected_revision": snapshot["script_revision"], "sentences": sentences},
        str(s["user_id"]),
        request.headers.get("idempotency-key"),
    )
    c.execute("UPDATE ai_draft_calls SET status='applied' WHERE id=%s", (id,))
    return result
