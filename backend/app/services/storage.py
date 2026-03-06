from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from uuid import uuid4

import boto3

from app.config import Settings


@lru_cache
def _s3_client(region: str):
    return boto3.client("s3", region_name=region)


@dataclass
class PresignedUpload:
    upload_url: str
    object_url: str
    expires_in: int
    key: str


def create_presigned_upload(
    settings: Settings,
    file_name: str,
    content_type: str,
    note_id: str | None,
    expires_in: int = 300,
) -> PresignedUpload:
    """Generate an upload target for either local or S3 storage."""
    prefix = f"notes/{note_id}" if note_id else "notes/misc"
    key = f"{prefix}/{uuid4()}-{file_name}"

    if settings.use_local_uploads:
        upload_url = f"{settings.api_base_url}/notes/upload/{key}"
        object_url = f"{settings.api_base_url}/static/{key}"
        return PresignedUpload(
            upload_url=upload_url,
            object_url=object_url,
            expires_in=expires_in,
            key=key,
        )

    # S3 path
    client = _s3_client(settings.aws_region)
    upload_url = client.generate_presigned_url(
        "put_object",
        Params={
            "Bucket": settings.s3_bucket,
            "Key": key,
            "ContentType": content_type,
        },
        ExpiresIn=expires_in,
    )
    object_url = f"https://{settings.s3_bucket}.s3.{settings.aws_region}.amazonaws.com/{key}"
    return PresignedUpload(
        upload_url=upload_url,
        object_url=object_url,
        expires_in=expires_in,
        key=key,
    )
