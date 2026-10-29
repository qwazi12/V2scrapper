"""Supabase Google PKCE flow with server-only tokens and an opaque owner session."""

import secrets
from datetime import timedelta
from urllib.parse import urlencode
from uuid import UUID
import httpx
from . import config, identity
from .db import insert, now
from .policy import require, PolicyError

LOGIN_COOKIE = "__Host-scos_supabase_login"


def start_login(c, response):
    require(config.auth_configured(), "AUTH_NOT_CONFIGURED", "Owner Google sign-in is not configured", 503)
    state, browser, verifier = (secrets.token_urlsafe(32) for _ in range(3))
    c.execute("DELETE FROM oidc_login_states WHERE expires_at<now()")
    insert(
        c,
        "oidc_login_states",
        state_hash=identity.token_hash(state),
        browser_hash=identity.token_hash(browser),
        nonce=secrets.token_urlsafe(32),
        code_verifier=verifier,
        expires_at=now() + timedelta(minutes=10),
    )
    response.set_cookie(
        LOGIN_COOKIE, state + "." + browser, secure=True, httponly=True, samesite="lax", path="/", max_age=600
    )
    return {
        "authorization_url": config.SUPABASE_URL
        + "/auth/v1/authorize?"
        + urlencode(
            {
                "provider": "google",
                "redirect_to": config.PUBLIC_URL + "/api/v1/auth/supabase/callback",
                "code_challenge": identity.pkce_challenge(verifier),
                "code_challenge_method": "s256",
                "scopes": "openid email profile",
            }
        ),
        "provider": "google",
        "state_expires_at": (now() + timedelta(minutes=10)).isoformat(),
    }


def verified_owner(user):
    # /user is an authenticated server-side validation, never an unverified JWT decode.
    try:
        subject = str(UUID(user["id"]))
        identities = user.get("identities", [])
        google = [i for i in identities if i.get("provider") == "google"]
        require(
            user.get("email", "").lower() == config.OWNER_EMAIL
            and bool(user.get("email_confirmed_at"))
            and any(
                i.get("identity_data", {}).get("email_verified") is True
                and i.get("identity_data", {}).get("email", "").lower() == config.OWNER_EMAIL
                for i in google
            ),
            "FORBIDDEN",
            "This verified Google account is not the configured owner",
            403,
        )
        require(not config.OWNER_SUBJECT or subject == config.OWNER_SUBJECT, "FORBIDDEN", "Owner subject mismatch", 403)
        return {"sub": subject, "email": config.OWNER_EMAIL}
    except (KeyError, TypeError, ValueError):
        raise PolicyError("AUTH_TOKEN_INVALID", "Supabase identity could not be verified", 403)


def exchange_code(code, state):
    try:
        headers = {"apikey": config.SUPABASE_ANON_KEY}
        with httpx.Client(timeout=15, follow_redirects=False) as client:
            r = client.post(
                config.SUPABASE_URL + "/auth/v1/token?grant_type=pkce",
                headers=headers,
                json={"auth_code": code, "code_verifier": state["code_verifier"]},
            )
            require(r.status_code == 200, "AUTH_EXCHANGE_FAILED", "Google sign-in exchange failed. Start again.", 403)
            token = r.json().get("access_token")
            require(
                isinstance(token, str) and 0 < len(token) <= 16384,
                "AUTH_TOKEN_INVALID",
                "Missing Supabase session",
                403,
            )
            user = client.get(
                config.SUPABASE_URL + "/auth/v1/user", headers={**headers, "Authorization": "Bearer " + token}
            )
            require(user.status_code == 200, "AUTH_TOKEN_INVALID", "Supabase session is invalid or revoked", 403)
            return verified_owner(user.json())
    except (httpx.HTTPError, ValueError):
        raise PolicyError("AUTH_PROVIDER_UNAVAILABLE", "Owner sign-in is temporarily unavailable", 503)
