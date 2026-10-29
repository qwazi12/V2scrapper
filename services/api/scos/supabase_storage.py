"""Private Supabase Storage adapter; duplicate uploads never overwrite existing bytes."""

import io
from urllib.parse import quote
import httpx
from botocore.exceptions import ClientError
from . import config


class SupabaseStorage:
    def request(self, method, path, **kwargs):
        with httpx.Client(timeout=120, follow_redirects=False) as client:
            response = client.request(
                method,
                config.SUPABASE_URL + "/storage/v1/" + path,
                headers={
                    "apikey": config.SUPABASE_SERVICE_KEY,
                    "Authorization": "Bearer " + config.SUPABASE_SERVICE_KEY,
                    **kwargs.pop("headers", {}),
                },
                **kwargs,
            )
        return response

    def head_bucket(self, Bucket):
        r = self.request("GET", "bucket/" + quote(Bucket, safe=""))
        if r.status_code != 200:
            raise ClientError(
                {"Error": {"Code": str(r.status_code), "Message": "Private bucket unavailable"}}, "HeadBucket"
            )
        if r.json().get("public") is not False:
            raise ValueError("SCOS_RESOURCE_ISOLATION: media bucket must be private")
        return {}

    def put_object(self, *, Bucket, Key, Body, IfNoneMatch, Metadata, ContentType):
        if IfNoneMatch != "*":
            raise ValueError("Immutable upload required")
        r = self.request(
            "POST",
            "object/" + quote(Bucket, safe="") + "/" + quote(Key, safe="/"),
            content=Body,
            headers={"Content-Type": ContentType, "x-upsert": "false"},
        )
        duplicate = r.status_code == 409 or (r.status_code == 400 and r.json().get("error") == "Duplicate")
        if duplicate:
            raise ClientError(
                {"Error": {"Code": "PreconditionFailed", "Message": "Object already exists"}}, "PutObject"
            )
        if r.status_code not in (200, 201):
            raise ClientError(
                {"Error": {"Code": str(r.status_code), "Message": "Private object upload failed"}}, "PutObject"
            )
        return {}

    def get_object(self, *, Bucket, Key):
        r = self.request("GET", "object/authenticated/" + quote(Bucket, safe="") + "/" + quote(Key, safe="/"))
        if r.status_code != 200:
            raise ClientError(
                {"Error": {"Code": str(r.status_code), "Message": "Private object read failed"}}, "GetObject"
            )
        return {"Body": io.BytesIO(r.content)}
