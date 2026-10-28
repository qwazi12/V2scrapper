import hashlib
import json
import time
from datetime import timedelta
import pytest
import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import Response
from fastapi.testclient import TestClient
from scos import config, identity
from scos.db import connect, insert, one, now
from scos.policy import PolicyError


@pytest.fixture
def signer(monkeypatch):
    monkeypatch.setattr(config, "OIDC_CLIENT_ID", "scos-test-client")
    monkeypatch.setattr(config, "OWNER_EMAIL", "owner@example.invalid")
    monkeypatch.setattr(config, "OWNER_SUBJECT", "")
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    jwk = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(key.public_key()))
    jwk.update(kid="test-google-key", alg="RS256", use="sig")
    claims = {
        "iss": config.OIDC_ISSUER,
        "aud": "scos-test-client",
        "sub": "stable-google-subject",
        "iat": int(time.time()),
        "exp": int(time.time()) + 600,
        "nonce": "test-nonce",
        "email": "owner@example.invalid",
        "email_verified": True,
    }
    return key, {"keys": [jwk]}, claims


def signed(key, claims):
    return jwt.encode(claims, key, algorithm="RS256", headers={"kid": "test-google-key"})


def test_owner_token_checks_signature_and_claims(signer):
    key, keys, claims = signer
    result = identity.verify_id_token(signed(key, claims), "test-nonce", keys)
    assert result["sub"] == "stable-google-subject"


@pytest.mark.parametrize(
    "field,value",
    [
        ("aud", "different-app"),
        ("iss", "https://attacker.example"),
        ("exp", 1),
        ("iat", 9999999999),
        ("nonce", "different-nonce"),
        ("email", "not-owner@example.invalid"),
        ("email_verified", False),
        ("email_verified", "true"),
        ("azp", "different-client"),
    ],
)
def test_token_mismatches_are_rejected(signer, field, value):
    key, keys, claims = signer
    claims[field] = value
    with pytest.raises(PolicyError):
        identity.verify_id_token(signed(key, claims), "test-nonce", keys)


def test_identity_signature_cannot_be_forged(signer):
    _, keys, claims = signer
    attacker = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    with pytest.raises(PolicyError):
        identity.verify_id_token(signed(attacker, claims), "test-nonce", keys)


def test_algorithm_confusion_rejected(signer):
    _, keys, claims = signer
    token = jwt.encode(claims, "attacker-secret", algorithm="HS256", headers={"kid": "test-google-key"})
    with pytest.raises(PolicyError):
        identity.verify_id_token(token, "test-nonce", keys)


def test_multiple_audiences_need_correct_authorized_party(signer):
    key, keys, claims = signer
    claims["aud"] = ["scos-test-client", "another-app"]
    with pytest.raises(PolicyError):
        identity.verify_id_token(signed(key, claims), "test-nonce", keys)


def test_pinned_owner_subject_blocks_other_google_identity(signer, monkeypatch):
    key, keys, claims = signer
    monkeypatch.setattr(config, "OWNER_SUBJECT", "different-owner-subject")
    with pytest.raises(PolicyError):
        identity.verify_id_token(signed(key, claims), "test-nonce", keys)


def save_state(expires=None):
    with connect() as c:
        insert(
            c,
            "oidc_login_states",
            state_hash=identity.token_hash("single-use-state"),
            browser_hash=identity.token_hash("browser-binding"),
            nonce="nonce",
            code_verifier="verifier",
            expires_at=expires or now() + timedelta(minutes=10),
        )


def test_state_consumption_is_single_use():
    save_state()
    assert identity.consume_state("single-use-state", "browser-binding")["nonce"] == "nonce"
    with pytest.raises(PolicyError):
        identity.consume_state("single-use-state", "browser-binding")


def test_state_requires_same_browser():
    save_state()
    with pytest.raises(PolicyError):
        identity.consume_state("single-use-state", "different-browser")
    assert identity.consume_state("single-use-state", "browser-binding")


def test_expired_login_is_rejected():
    save_state(now() - timedelta(seconds=1))
    with pytest.raises(PolicyError):
        identity.consume_state("single-use-state", "browser-binding")


def test_owner_is_bound_to_stable_google_subject(conn):
    conn.execute("DELETE FROM app_users WHERE id=%s", (config.OWNER_ID,))
    first = identity.owner_from_identity(conn, {"sub": "subject-a", "email": "owner@example.invalid"})
    assert first["role"] == "owner"
    with pytest.raises(PolicyError):
        identity.owner_from_identity(conn, {"sub": "subject-b", "email": "owner@example.invalid"})


def test_hosted_sessions_use_secure_host_cookie(conn, monkeypatch):
    monkeypatch.setattr(config, "HOSTED", True)
    monkeypatch.setattr(config, "SESSION_COOKIE", "__Host-scos_session")
    response = Response()
    csrf = identity.issue_session(conn, response, config.OWNER_ID)
    cookie = response.headers["set-cookie"]
    assert "__Host-scos_session=" in cookie and "Secure" in cookie and "HttpOnly" in cookie and "Path=/" in cookie
    assert "Domain=" not in cookie
    row = one(conn, "SELECT * FROM sessions")
    assert bytes(row["csrf_hash"]) == hashlib.sha256(csrf.encode()).digest()


def test_staging_cannot_use_development_login(monkeypatch):
    import scos.app as api

    monkeypatch.setattr(api, "ENV", "staging")
    with TestClient(api.app) as client:
        response = client.post("/api/v1/auth/local", headers={"Origin": "http://127.0.0.1:3100"})
        assert response.status_code == 403


def test_unconfigured_oidc_is_fail_closed():
    from scos.app import app

    with TestClient(app) as client:
        response = client.get("/api/v1/auth/oidc/start")
        assert response.status_code == 503


def test_migration_has_login_state_table(conn):
    assert one(conn, "SELECT to_regclass('public.oidc_login_states') AS t")["t"] == "oidc_login_states"
