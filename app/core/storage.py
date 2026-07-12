import os
from pathlib import Path
from uuid import uuid4

import boto3
from botocore.config import Config
from fastapi import HTTPException, UploadFile

from app.core.config import settings


class R2StorageService:
    def __init__(self) -> None:
        self.access_key_id = settings.R2_ACCESS_KEY_ID
        self.secret_access_key = settings.R2_SECRET_ACCESS_KEY
        self.bucket_name = settings.R2_BUCKET_NAME
        self.endpoint_url = settings.R2_ENDPOINT_URL
        self.public_url = settings.R2_PUBLIC_URL
        self.account_id = settings.R2_ACCOUNT_ID
        self.region = settings.R2_REGION
        self._client = None

    @property
    def is_configured(self) -> bool:
        return bool(
            self.access_key_id
            and self.secret_access_key
            and self.bucket_name
            and self.endpoint_url
        )

    def _get_client(self):
        if not self.is_configured:
            return None

        if self._client is None:
            self._client = boto3.client(
                "s3",
                region_name=self.region,
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.access_key_id,
                aws_secret_access_key=self.secret_access_key,
                config=Config(signature_version="s3v4"),
            )

        return self._client

    async def upload_file(self, file: UploadFile, folder: str) -> str | None:
        if file is None:
            return None

        if not self.is_configured:
            raise HTTPException(
                status_code=500,
                detail="Cloudflare R2 storage is not configured. Set R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET_NAME, and R2_ENDPOINT_URL in your environment.",
            )

        if not getattr(file, "filename", None):
            return None

        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")

        extension = Path(file.filename).suffix.lower() or ".bin"
        key = f"{folder}/{uuid4().hex}{extension}"

        client = self._get_client()
        try:
            client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=content,
                ContentType=file.content_type or "application/octet-stream",
            )
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"R2 upload failed: {exc}") from exc

        if self.public_url:
            return f"{self.public_url.rstrip('/')}/{key}"

        if self.account_id:
            return f"https://{self.bucket_name}.{self.account_id}.r2.cloudflarestorage.com/{key}"

        return f"{self.endpoint_url.rstrip('/')}/{self.bucket_name}/{key}"

    async def upload_image(self, file: UploadFile, folder: str) -> str:
        return await self.upload_file(file, folder)


storage_service = R2StorageService()
