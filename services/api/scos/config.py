import os
import re
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[3]
ENV = os.getenv("SCOS_ENV", "local")
HOSTED = ENV in ("staging", "production")
DATA_PROVIDER = os.getenv("SCOS_DATA_PROVIDER", "railway")
SUPABASE_REF = os.getenv("SCOS_SUPABASE_PROJECT_REF", "")
SUPABASE_URL = os.getenv("SCOS_SUPABASE_URL", "").rstrip("/")
SUPABASE_ANON_KEY = os.getenv("SCOS_SUPABASE_ANON_KEY", "")
SUPABASE_SERVICE_KEY = os.getenv("SCOS_SUPABASE_SERVICE_KEY", "")
SUPABASE_GOOGLE_ENABLED = os.getenv("SCOS_SUPABASE_GOOGLE_ENABLED", "false") == "true"
DATABASE_SCHEMA = os.getenv("SCOS_DATABASE_SCHEMA", "public")
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
    if DATA_PROVIDER == "supabase":
        return bool(SUPABASE_URL and SUPABASE_ANON_KEY and SUPABASE_GOOGLE_ENABLED and OWNER_EMAIL)
    return bool(OIDC_CLIENT_ID and OIDC_CLIENT_SECRET and OWNER_EMAIL)


def database_connect_args():
    args = {"options": "-csearch_path=" + DATABASE_SCHEMA + ",public"} if DATABASE_SCHEMA != "public" else {}
    if DATA_PROVIDER == "supabase":
        args.update(sslmode="verify-full", sslrootcert=str(ROOT / "certs/supabase-prod-ca-2021.crt"))
    return args


def validate():
    if ENV not in ("local", "ci", "staging", "production"):
        raise RuntimeError("SCOS_RESOURCE_ISOLATION: unknown environment")
    if "scrapper" in DATABASE_URL.lower() or not BUCKET.startswith("scos-") or NAMESPACE != "scos-" + ENV:
        raise RuntimeError("SCOS_RESOURCE_ISOLATION: refusing non-SCOS resources")
    database = urlparse(DATABASE_URL)
    store = urlparse(S3_ENDPOINT)
    if DATA_PROVIDER not in ("railway", "supabase") or not re.fullmatch(r"[a-z_][a-z0-9_]*", DATABASE_SCHEMA):
        raise RuntimeError("Invalid data provider or database schema")
    if ENV not in ("staging", "production"):
        if "scos" not in database.path or database.hostname not in ("127.0.0.1", "localhost", "postgres"):
            raise RuntimeError("SCOS_RESOURCE_ISOLATION: local database only")
        if store.hostname not in ("127.0.0.1", "localhost", "s3mock"):
            raise RuntimeError("SCOS_RESOURCE_ISOLATION: local storage only")
    else:
        if DATA_PROVIDER == "supabase":
            from urllib.parse import parse_qs

            expected_schema = "scos_" + ENV
            direct_host = "db." + SUPABASE_REF + ".supabase.co"
            pooler = bool(re.fullmatch(r"aws-\d+-[a-z0-9-]+\.pooler\.supabase\.com", database.hostname or ""))
            pinned_user = (database.username or "").endswith("." + SUPABASE_REF)
            if (
                not re.fullmatch(r"[a-z]{20}", SUPABASE_REF)
                or SUPABASE_URL != "https://" + SUPABASE_REF + ".supabase.co"
                or not (database.hostname == direct_host or (pooler and pinned_user))
                or database.path != "/postgres"
                or DATABASE_SCHEMA != expected_schema
                or parse_qs(database.query).get("sslmode", [None])[0] not in ("require", "verify-full")
                or not SUPABASE_SERVICE_KEY
            ):
                raise RuntimeError("SCOS_RESOURCE_ISOLATION: Supabase project, private schema and TLS must be pinned")
        elif database.path != ("/scos_staging" if ENV == "staging" else "/scos_prod"):
            raise RuntimeError("SCOS_RESOURCE_ISOLATION: hosted database must match the environment")
        if database.hostname in ("127.0.0.1", "localhost", "postgres"):
            raise RuntimeError("SCOS_RESOURCE_ISOLATION: hosted app cannot use the development database")
        if urlparse(PUBLIC_URL).scheme != "https" or (DATA_PROVIDER != "supabase" and store.scheme != "https"):
            raise RuntimeError("Hosted application and object storage require HTTPS")
        if DATA_PROVIDER != "supabase" and not all(
            os.getenv(name) for name in ("SCOS_S3_ACCESS_KEY_ID", "SCOS_S3_SECRET_ACCESS_KEY")
        ):
            raise RuntimeError("Hosted private object-store credentials are required")
        if not BUCKET.startswith("scos-" + ENV):
            raise RuntimeError("SCOS_RESOURCE_ISOLATION: bucket must match the environment")
        if ENV == "production" and not auth_configured():
            raise RuntimeError("Production requires configured owner OIDC before startup")
    RUNTIME.mkdir(parents=True, exist_ok=True)
