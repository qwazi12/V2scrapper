"""Owner-only Google OIDC. No social scopes, refresh tokens, or social grants are requested."""

import base64
import hashlib
import secrets
from datetime import timedelta
from urllib.parse import urlencode
import httpx
import jwt
from . import config
from .db import connect, one, insert, now, audit
from .policy import require, PolicyError

AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
JWKS_URL = "https://www.googleapis.com/oauth2/v3/certs"
LOGIN_COOKIE = "__Host-scos_login"


def token_hash(text):
    return hashlib.sha256(text.encode()).digest()


def pkce_challenge(verifier):
    return base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()


def issue_session(c, response, user_id, environment=None):
    token = secrets.token_urlsafe(32)
    csrf = hashlib.sha256(("csrf:" + token).encode()).hexdigest()
    insert(
        c,
        "sessions",
        user_id=user_id,
        token_hash=token_hash(token),
        csrf_hash=token_hash(csrf),
        expires_at=now() + timedelta(hours=12),
    )
    response.set_cookie(
        config.SESSION_COOKIE,
        token,
        httponly=True,
        samesite="lax" if config.HOSTED else "strict",
        secure=config.HOSTED,
        path="/",
        max_age=43200,
    )
    audit(c, "session.created", user_id, str(user_id), details={"environment": environment or config.ENV})
    return csrf


def start_login(c, response):
    require(
        config.auth_configured(),
        "AUTH_NOT_CONFIGURED",
        "Owner Google sign-in needs a new OAuth client and owner allowlist.",
        503,
    )
    state, browser, nonce, verifier = (secrets.token_urlsafe(32) for _ in range(4))
    c.execute("DELETE FROM oidc_login_states WHERE expires_at<now()")
    insert(
        c,
        "oidc_login_states",
        state_hash=token_hash(state),
        browser_hash=token_hash(browser),
        nonce=nonce,
        code_verifier=verifier,
        expires_at=now() + timedelta(minutes=10),
    )
    response.set_cookie(LOGIN_COOKIE, browser, secure=True, httponly=True, samesite="lax", path="/", max_age=600)
    return {
        "authorization_url": AUTHORIZE_URL
        + "?"
        + urlencode(
            {
                "client_id": config.OIDC_CLIENT_ID,
                "redirect_uri": config.OIDC_REDIRECT_URI,
                "response_type": "code",
                "scope": "openid email profile",
                "state": state,
                "nonce": nonce,
                "code_challenge": pkce_challenge(verifier),
                "code_challenge_method": "S256",
                "prompt": "select_account",
            }
        ),
        "provider": "google",
        "state_expires_at": (now() + timedelta(minutes=10)).isoformat(),
    }


def consume_state(state, browser):
    # Commit consumption before contacting the token endpoint. A failed exchange requires a fresh login.
    with connect() as c:
        row = one(c, "SELECT * FROM oidc_login_states WHERE state_hash=%s FOR UPDATE", (token_hash(state),))
        require(
            row
            and row["used_at"] is None
            and row["expires_at"] > now()
            and secrets.compare_digest(bytes(row["browser_hash"]), token_hash(browser)),
            "AUTH_STATE_INVALID",
            "Sign-in state is invalid, expired, or already used. Start again.",
            403,
        )
        c.execute("UPDATE oidc_login_states SET used_at=now() WHERE state_hash=%s", (row["state_hash"],))
        return row


def verify_id_token(id_token, nonce, jwks):
    try:
        header = jwt.get_unverified_header(id_token)
        require(header.get("alg") == "RS256", "AUTH_TOKEN_INVALID", "Unsupported ID token algorithm", 403)
        keys = [
            key
            for key in jwks.get("keys", [])
            if key.get("kid") == header.get("kid")
            and key.get("kty") == "RSA"
            and key.get("use", "sig") == "sig"
            and key.get("alg", "RS256") == "RS256"
        ]
        require(len(keys) == 1, "AUTH_TOKEN_INVALID", "No matching Google signing key", 403)
        key = jwt.PyJWK.from_dict(keys[0], algorithm="RS256").key
        claims = jwt.decode(
            id_token,
            key,
            algorithms=["RS256"],
            audience=config.OIDC_CLIENT_ID,
            issuer=config.OIDC_ISSUER,
            options={"require": ["exp", "iat", "iss", "aud", "sub", "nonce", "email", "email_verified"]},
        )
        require(
            isinstance(claims.get("nonce"), str) and secrets.compare_digest(claims["nonce"], nonce),
            "AUTH_TOKEN_INVALID",
            "Sign-in nonce mismatch",
            403,
        )
        require(
            claims.get("email_verified") is True and claims["email"].lower() == config.OWNER_EMAIL,
            "FORBIDDEN",
            "This Google account is not the configured owner",
            403,
        )
        require(
            not config.OWNER_SUBJECT or claims["sub"] == config.OWNER_SUBJECT,
            "FORBIDDEN",
            "Google subject is not the configured owner",
            403,
        )
        require(
            not claims.get("azp") or claims["azp"] == config.OIDC_CLIENT_ID,
            "AUTH_TOKEN_INVALID",
            "Authorized party mismatch",
            403,
        )
        require(
            not isinstance(claims["aud"], list)
            or len(claims["aud"]) == 1
            or claims.get("azp") == config.OIDC_CLIENT_ID,
            "AUTH_TOKEN_INVALID",
            "Multiple-audience token requires the expected authorized party",
            403,
        )
        return claims
    except jwt.PyJWTError:
        raise PolicyError("AUTH_TOKEN_INVALID", "Google identity could not be verified", 403)


def exchange_code(code, state):
    try:
        with httpx.Client(timeout=15, follow_redirects=False) as client:
            response = client.post(
                TOKEN_URL,
                data={
                    "code": code,
                    "client_id": config.OIDC_CLIENT_ID,
                    "client_secret": config.OIDC_CLIENT_SECRET,
                    "redirect_uri": config.OIDC_REDIRECT_URI,
                    "grant_type": "authorization_code",
                    "code_verifier": state["code_verifier"],
                },
            )
            require(
                response.status_code == 200, "AUTH_EXCHANGE_FAILED", "Google sign-in exchange failed. Start again.", 403
            )
            token = response.json().get("id_token")
            require(isinstance(token, str), "AUTH_TOKEN_INVALID", "Google did not return an identity token", 403)
            keys = client.get(JWKS_URL)
            require(keys.status_code == 200, "AUTH_PROVIDER_UNAVAILABLE", "Google signing keys are unavailable", 503)
            return verify_id_token(token, state["nonce"], keys.json())
    except (httpx.HTTPError, ValueError):
        raise PolicyError("AUTH_PROVIDER_UNAVAILABLE", "Google sign-in is temporarily unavailable", 503)


def owner_from_identity(c, claims):
    subject = config.OIDC_ISSUER + "|" + claims["sub"]
    c.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s,0))", ("scos:owner-identity",))
    existing = one(c, "SELECT * FROM app_users WHERE id=%s FOR UPDATE", (config.OWNER_ID,))
    if existing:
        require(
            existing["active"] and existing["auth_subject"] == subject and existing["role"] == "owner",
            "FORBIDDEN",
            "Owner identity is already bound to a different Google subject",
            403,
        )
        return existing
    return insert(
        c,
        "app_users",
        id=config.OWNER_ID,
        email=claims["email"].lower(),
        display_name="Screen Central",
        auth_subject=subject,
        role="owner",
    )
