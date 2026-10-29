import json
from urllib.parse import parse_qs, urlparse
from uuid import uuid4
import httpx
import pytest
from fastapi import Response
from fastapi.testclient import TestClient
from botocore.exceptions import ClientError
from scos import config, identity, supabase_auth
from scos.app import app
from scos.db import connect
from scos.policy import PolicyError
from scos.supabase_storage import SupabaseStorage


def test_missing_private_schema_cannot_fall_back_to_public(monkeypatch):
    from scos import db

    monkeypatch.setattr(db, "DATABASE_SCHEMA", "scos_nonexistent_test_schema")
    with pytest.raises(RuntimeError, match="private database schema is missing"):
        db.connect()


@pytest.fixture
def supa(monkeypatch):
    from scos import db

    # Identity transport is mocked; the test ledger stays on its separate local PostgreSQL instance.
    monkeypatch.setattr(db, "database_connect_args", lambda: {})
    monkeypatch.setattr(config, "DATA_PROVIDER", "supabase")
    monkeypatch.setattr(config, "SUPABASE_URL", "https://abcdefghijklmnopqrst.supabase.co")
    monkeypatch.setattr(config, "SUPABASE_ANON_KEY", "public-test-key")
    monkeypatch.setattr(config, "SUPABASE_GOOGLE_ENABLED", True)
    monkeypatch.setattr(config, "OWNER_EMAIL", "owner@example.invalid")
    monkeypatch.setattr(config, "OWNER_SUBJECT", "")
    monkeypatch.setattr(config, "PUBLIC_URL", "https://staging.example.invalid")


def google_user():
    return {
        "id": str(uuid4()),
        "email": "owner@example.invalid",
        "email_confirmed_at": "2026-01-01T00:00:00Z",
        "identities": [
            {"provider": "google", "identity_data": {"email": "owner@example.invalid", "email_verified": True}}
        ],
    }


def test_supabase_login_uses_pkce_and_secure_browser_binding(supa):
    response = Response()
    with connect() as c:
        result = supabase_auth.start_login(c, response)
    cookie = response.headers["set-cookie"]
    assert "Secure" in cookie and "HttpOnly" in cookie and "Path=/" in cookie
    binding = cookie.split(";", 1)[0].split("=", 1)[1]
    state, browser = binding.split(".")
    row = identity.consume_state(state, browser)
    query = parse_qs(urlparse(result["authorization_url"]).query)
    assert query["code_challenge"] == [identity.pkce_challenge(row["code_verifier"])]
    assert query["redirect_to"] == ["https://staging.example.invalid/api/v1/auth/supabase/callback"]
    assert query["provider"] == ["google"]
    assert "secret" not in result["authorization_url"]
    with pytest.raises(PolicyError):
        identity.consume_state(state, browser)


@pytest.mark.parametrize("alter", ["email", "unconfirmed", "provider", "unverified", "identity_email", "bad_id"])
def test_supabase_rejects_non_owner_and_unverified_identity(supa, alter):
    user = google_user()
    if alter == "email":
        user["email"] = "attacker@example.invalid"
    if alter == "unconfirmed":
        user["email_confirmed_at"] = None
    if alter == "provider":
        user["identities"][0]["provider"] = "email"
    if alter == "unverified":
        user["identities"][0]["identity_data"]["email_verified"] = False
    if alter == "identity_email":
        user["identities"][0]["identity_data"]["email"] = "attacker@example.invalid"
    if alter == "bad_id":
        user["id"] = "not-a-user-id"
    with pytest.raises(PolicyError):
        supabase_auth.verified_owner(user)


def test_supabase_exchange_validates_user_server_side(supa, monkeypatch):
    user = google_user()
    seen = []
    client_type = httpx.Client

    def handler(request):
        seen.append(request)
        if request.url.path.endswith("/token"):
            assert request.url.params["grant_type"] == "pkce"
            assert json.loads(request.content) == {"auth_code": "one-use-code", "code_verifier": "verifier"}
            return httpx.Response(200, json={"access_token": "server-only-token", "refresh_token": "discarded"})
        assert request.headers["authorization"] == "Bearer server-only-token"
        return httpx.Response(200, json=user)

    monkeypatch.setattr(
        supabase_auth.httpx, "Client", lambda **kw: client_type(transport=httpx.MockTransport(handler), **kw)
    )
    claims = supabase_auth.exchange_code("one-use-code", {"code_verifier": "verifier"})
    assert claims == {"sub": user["id"], "email": "owner@example.invalid"}
    assert len(seen) == 2
    assert all(r.headers["apikey"] == "public-test-key" for r in seen)


def test_supabase_revoked_token_rejected(supa, monkeypatch):
    client_type = httpx.Client

    def handler(request):
        return (
            httpx.Response(200, json={"access_token": "revoked"})
            if request.url.path.endswith("/token")
            else httpx.Response(401)
        )

    monkeypatch.setattr(
        supabase_auth.httpx, "Client", lambda **kw: client_type(transport=httpx.MockTransport(handler), **kw)
    )
    with pytest.raises(PolicyError):
        supabase_auth.exchange_code("code", {"code_verifier": "verifier"})


def test_supabase_callback_requires_browser_cookie(supa):
    client = TestClient(app)
    assert client.get("/api/v1/auth/supabase/callback?code=stolen-code").status_code == 403


def test_supabase_owner_binding_uses_project_issuer(supa):
    with connect() as c:
        c.execute("DELETE FROM app_users WHERE id=%s", (config.OWNER_ID,))
        user = google_user()
        claims = supabase_auth.verified_owner(user)
        result = identity.owner_from_identity(c, claims, issuer=config.SUPABASE_URL + "/auth/v1")
        assert result["auth_subject"] == config.SUPABASE_URL + "/auth/v1|" + user["id"]
        with pytest.raises(PolicyError):
            identity.owner_from_identity(c, {**claims, "sub": str(uuid4())}, issuer=config.SUPABASE_URL + "/auth/v1")


def test_supabase_private_bucket_required(monkeypatch):
    storage = SupabaseStorage()
    monkeypatch.setattr(storage, "request", lambda *a, **kw: httpx.Response(200, json={"public": True}))
    with pytest.raises(ValueError):
        storage.head_bucket(Bucket="scos-staging-media")


def test_supabase_upload_never_upserts(monkeypatch):
    storage = SupabaseStorage()

    def request(method, path, **kw):
        assert method == "POST" and kw["headers"]["x-upsert"] == "false"
        return httpx.Response(409, json={"error": "Duplicate"})

    monkeypatch.setattr(storage, "request", request)
    with pytest.raises(ClientError) as error:
        storage.put_object(
            Bucket="scos-staging-media",
            Key="objects/hash.txt",
            Body=b"bytes",
            IfNoneMatch="*",
            Metadata={},
            ContentType="text/plain",
        )
    assert error.value.response["Error"]["Code"] == "PreconditionFailed"
