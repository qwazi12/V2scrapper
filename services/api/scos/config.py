import os
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[3]
ENV = os.getenv("SCOS_ENV", "local")
DATABASE_URL = os.getenv("SCOS_DATABASE_URL", "postgresql://scos:scos_local_only@127.0.0.1:55432/scos_local")
S3_ENDPOINT = os.getenv("SCOS_S3_ENDPOINT", "http://127.0.0.1:59000")
BUCKET = os.getenv("SCOS_S3_BUCKET", "scos-local")
ORIGINS = {"http://127.0.0.1:3100", "http://localhost:3100"}
RUNTIME = ROOT / ".runtime"
OWNER_ID = "11111111-1111-4111-8111-111111111111"


def validate():
    if ENV not in ("local", "ci"):
        raise RuntimeError("This build supports isolated local/CI only; production OIDC is not implemented.")
    if "scos" not in DATABASE_URL or "scrapper" in DATABASE_URL.lower() or not BUCKET.startswith("scos-"):
        raise RuntimeError("SCOS_RESOURCE_ISOLATION: refusing non-SCOS resources")
    if urlparse(DATABASE_URL).hostname not in ("127.0.0.1", "localhost", "postgres"):
        raise RuntimeError("SCOS_RESOURCE_ISOLATION: local database only")
    if urlparse(S3_ENDPOINT).hostname not in ("127.0.0.1", "localhost", "s3mock"):
        raise RuntimeError("SCOS_RESOURCE_ISOLATION: local storage only")
    RUNTIME.mkdir(exist_ok=True)
