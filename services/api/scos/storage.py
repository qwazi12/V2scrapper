import mimetypes
import os
from pathlib import Path
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from .config import BUCKET, RUNTIME, S3_ENDPOINT, HOSTED
from .db import sha


def client():
    return boto3.client(
        "s3",
        endpoint_url=S3_ENDPOINT,
        region_name=os.getenv("SCOS_S3_REGION", "auto" if HOSTED else "us-east-1"),
        aws_access_key_id=os.getenv("SCOS_S3_ACCESS_KEY_ID", "scos_local"),
        aws_secret_access_key=os.getenv("SCOS_S3_SECRET_ACCESS_KEY", "scos_local_only"),
        config=Config(
            signature_version="s3v4",
            connect_timeout=10,
            read_timeout=30,
            retries={"max_attempts": 3, "mode": "standard"},
            s3={"addressing_style": os.getenv("SCOS_S3_ADDRESSING_STYLE", "path")},
        ),
    )


def init():
    s3 = client()
    try:
        s3.head_bucket(Bucket=BUCKET)
    except ClientError as exc:
        if HOSTED or str(exc.response.get("Error", {}).get("Code")) not in ("404", "NoSuchBucket", "NotFound"):
            raise
        s3.create_bucket(Bucket=BUCKET)


def safe_key(key):
    import re

    if not re.fullmatch(r"objects/[0-9a-f]{64}\.[a-z0-9]+", key):
        raise ValueError("Invalid content-addressed object key")
    path = RUNTIME / key
    if not path.resolve().is_relative_to((RUNTIME / "objects").resolve()):
        raise ValueError("Invalid object key")
    return path


def put(path: Path):
    data = path.read_bytes()
    digest = sha(data)
    key = f"objects/{digest}{path.suffix.lower()}"
    mirror = safe_key(key)
    s3 = client()
    try:
        # Concurrent identical content may converge on the same immutable object.
        s3.put_object(
            Bucket=BUCKET,
            Key=key,
            Body=data,
            IfNoneMatch="*",
            Metadata={"sha256": digest},
            ContentType=mimetypes.guess_type(path.name)[0] or "application/octet-stream",
        )
    except ClientError as exc:
        if exc.response.get("Error", {}).get("Code") not in ("PreconditionFailed", "412"):
            raise
        remote = s3.get_object(Bucket=BUCKET, Key=key)["Body"].read()
        if sha(remote) != digest:
            raise ValueError("ASSET_MISMATCH: immutable object already exists with different bytes")
    if not HOSTED:
        mirror.parent.mkdir(parents=True, exist_ok=True)
        if not mirror.exists():
            mirror.write_bytes(data)
    return key, digest, len(data)


def read(key, expected_hash=None):
    mirror = safe_key(key)
    # Hosted reads always use durable S3; an ephemeral render filesystem is never authoritative.
    if not HOSTED and mirror.exists():
        data = mirror.read_bytes()
    else:
        data = client().get_object(Bucket=BUCKET, Key=key)["Body"].read()
    expected = expected_hash or key.split("/")[1].split(".")[0]
    if sha(data) != expected:
        raise ValueError("ASSET_MISMATCH: object checksum failed")
    return data
