import os
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[3]
ENV = os.getenv("SCOS_ENV", "local")
HOSTED = ENV in ("staging", "production")
NAMESPACE = os.getenv("SCOS_RESOURCE_NAMESPACE", "scos-" + ENV)
DATABASE_URL = os.getenv("SCOS_DATABASE_URL", "postgresql://scos:scos_local_only@127.0.0.1:55432/scos_local")
S3_ENDPOINT = os.getenv("SCOS_S3_ENDPOINT", "http://127.0.0.1:59000")
BUCKET = os.getenv("SCOS_S3_BUCKET", "scos-local")
PUBLIC_URL = os.getenv(
    "SCOS_PUBLIC_URL", "http://127.0.0.1:3101" if "staging" in ROOT.name else "http://127.0.0.1:3100"
).rstrip("/")
ORIGINS = (
    {PUBLIC_URL}
    if HOSTED
    else {"http://127.0.0.1:3100", "http://localhost:3100", "http://127.0.0.1:3101", "http://localhost:3101"}
)
RUNTIME = Path(os.getenv("SCOS_RUNTIME_DIR", str(ROOT / ".runtime")))
OWNER_ID = "11111111-1111-4111-8111-111111111111"
SESSION_COOKIE = "__Host-scos_session" if HOSTED else "scos_session"
OIDC_ISSUER = "https://accounts.google.com"
OIDC_CLIENT_ID = os.getenv("SCOS_OIDC_CLIENT_ID", "")
OIDC_CLIENT_SECRET = os.getenv("SCOS_OIDC_CLIENT_SECRET", "")
OWNER_EMAIL = os.getenv("SCOS_OWNER_EMAIL", "").strip().lower()
OWNER_SUBJECT = os.getenv("SCOS_OWNER_SUBJECT", "")
OIDC_REDIRECT_URI = PUBLIC_URL + "/api/v1/auth/oidc/callback"


def auth_configured():
    return bool(OIDC_CLIENT_ID and OIDC_CLIENT_SECRET and OWNER_EMAIL)


def validate():
    if ENV not in ("local", "ci", "staging", "production"):
        raise RuntimeError("SCOS_RESOURCE_ISOLATION: unknown environment")
    if "scrapper" in DATABASE_URL.lower() or not BUCKET.startswith("scos-") or NAMESPACE != "scos-" + ENV:
        raise RuntimeError("SCOS_RESOURCE_ISOLATION: refusing non-SCOS resources")
    database = urlparse(DATABASE_URL)
    store = urlparse(S3_ENDPOINT)
    if ENV not in ("staging", "production"):
        if "scos" not in database.path or database.hostname not in ("127.0.0.1", "localhost", "postgres"):
            raise RuntimeError("SCOS_RESOURCE_ISOLATION: local database only")
        if store.hostname not in ("127.0.0.1", "localhost", "s3mock"):
            raise RuntimeError("SCOS_RESOURCE_ISOLATION: local storage only")
    else:
        if database.path != ("/scos_staging" if ENV == "staging" else "/scos_prod"):
            raise RuntimeError("SCOS_RESOURCE_ISOLATION: hosted database must match the environment")
        if database.hostname in ("127.0.0.1", "localhost", "postgres"):
            raise RuntimeError("SCOS_RESOURCE_ISOLATION: hosted app cannot use the development database")
        if urlparse(PUBLIC_URL).scheme != "https" or store.scheme != "https":
            raise RuntimeError("Hosted application and object storage require HTTPS")
        if not all(os.getenv(name) for name in ("SCOS_S3_ACCESS_KEY_ID", "SCOS_S3_SECRET_ACCESS_KEY")):
            raise RuntimeError("Hosted private object-store credentials are required")
        if not BUCKET.startswith("scos-" + ENV):
            raise RuntimeError("SCOS_RESOURCE_ISOLATION: bucket must match the environment")
        if ENV == "production" and not auth_configured():
            raise RuntimeError("Production requires configured owner OIDC before startup")
    RUNTIME.mkdir(parents=True, exist_ok=True)
