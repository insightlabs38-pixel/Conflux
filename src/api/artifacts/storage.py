import math

import boto3
from botocore.config import Config
from django.conf import settings

PART_SIZE = 8 * 1024 * 1024
MULTIPART_THRESHOLD = 16 * 1024 * 1024
MAX_PARTS = 100


class S3Storage:
    def __init__(
        self, *, endpoint=None, public_endpoint=None, bucket=None, access_key=None, secret_key=None
    ):
        self.endpoint = endpoint or settings.S3_ENDPOINT_URL
        self.public_endpoint = public_endpoint or settings.S3_PUBLIC_ENDPOINT_URL
        self.bucket = bucket or settings.S3_BUCKET_NAME
        self.access_key = access_key or settings.S3_ACCESS_KEY
        self.secret_key = secret_key or settings.S3_SECRET_KEY
        self.client = self._client(self.endpoint)

    def _client(self, endpoint):
        return boto3.client(
            "s3",
            endpoint_url=endpoint,
            region_name="us-east-1",
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
        )

    def ensure_bucket(self):
        from botocore.exceptions import ClientError

        try:
            self.client.head_bucket(Bucket=self.bucket)
        except ClientError as exc:
            if exc.response["Error"]["Code"] not in {"404", "NoSuchBucket", "NotFound"}:
                raise
            self.client.create_bucket(Bucket=self.bucket)

    def presign_put(self, key, content_type, artifact_id, expires):
        public = self._client(self.public_endpoint)
        return public.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": self.bucket,
                "Key": key,
                "ContentType": content_type,
                "Metadata": {"artifact-id": artifact_id},
            },
            ExpiresIn=expires,
        )

    def presign_get(self, key, expires=300):
        return self._client(self.public_endpoint).generate_presigned_url(
            "get_object", Params={"Bucket": self.bucket, "Key": key}, ExpiresIn=expires
        )

    def start_multipart(self, key, content_type, artifact_id, size, expires):
        count = math.ceil(size / PART_SIZE)
        if count > MAX_PARTS:
            raise ValueError("Upload exceeds the multipart limit.")
        result = self.client.create_multipart_upload(
            Bucket=self.bucket,
            Key=key,
            ContentType=content_type,
            Metadata={"artifact-id": artifact_id},
        )
        upload_id = result["UploadId"]
        public = self._client(self.public_endpoint)
        urls = [
            public.generate_presigned_url(
                "upload_part",
                Params={
                    "Bucket": self.bucket,
                    "Key": key,
                    "UploadId": upload_id,
                    "PartNumber": part,
                },
                ExpiresIn=expires,
            )
            for part in range(1, count + 1)
        ]
        return upload_id, urls

    def complete_multipart(self, key, upload_id, parts):
        return self.client.complete_multipart_upload(
            Bucket=self.bucket,
            Key=key,
            UploadId=upload_id,
            MultipartUpload={"Parts": parts},
        )

    def abort_multipart(self, key, upload_id):
        self.client.abort_multipart_upload(Bucket=self.bucket, Key=key, UploadId=upload_id)

    def head(self, key):
        return self.client.head_object(Bucket=self.bucket, Key=key)

    def get(self, key):
        return self.client.get_object(Bucket=self.bucket, Key=key)

    def put(self, key, data, *, content_type="application/octet-stream", metadata=None):
        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
            Metadata=metadata or {},
        )

    def delete(self, key):
        self.client.delete_object(Bucket=self.bucket, Key=key)

    def list_prefix(self, prefix):
        return self.client.list_objects_v2(Bucket=self.bucket, Prefix=prefix).get("Contents", [])
