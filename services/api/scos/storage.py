import mimetypes
import os
from pathlib import Path
import boto3
from botocore.exceptions import ClientError
from .config import BUCKET, RUNTIME, S3_ENDPOINT
from .db import sha


def client():
    return boto3.client(
        "s3",
        endpoint_url=S3_ENDPOINT,
        region_name="us-east-1",
        aws_access_key_id=os.getenv("SCOS_S3_ACCESS_KEY_ID", "scos_local"),
        aws_secret_access_key=os.getenv("SCOS_S3_SECRET_ACCESS_KEY", "scos_local_only"),
    )


def init():
    s3 = client()
    try:
        s3.head_bucket(Bucket=BUCKET)
    except ClientError:
        s3.create_bucket(Bucket=BUCKET)


def put(path: Path):
    data = path.read_bytes()
    key = f"objects/{sha(data)}{path.suffix.lower()}"
    mirror = RUNTIME / key
    mirror.parent.mkdir(parents=True, exist_ok=True)
    if not mirror.exists():
        mirror.write_bytes(data)
    client().put_object(
        Bucket=BUCKET, Key=key, Body=data, ContentType=mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    )
    return key, sha(data), len(data)


def read(key, expected_hash=None):
    # Only called with a key from an authorized DB record, never a user path.
    mirror = RUNTIME / key
    if not mirror.resolve().is_relative_to((RUNTIME / "objects").resolve()):
        raise ValueError("Invalid object key")
    if mirror.exists():
        data = mirror.read_bytes()
    else:
        data = client().get_object(Bucket=BUCKET, Key=key)["Body"].read()
    if expected_hash and sha(data) != expected_hash:
        raise ValueError("ASSET_MISMATCH: object checksum failed")
    return data
