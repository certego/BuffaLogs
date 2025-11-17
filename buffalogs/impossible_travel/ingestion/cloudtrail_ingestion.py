import json
import gzip
import boto3  # type: ignore
from .base_ingestion import BaseIngestion


class CloudTrailIngestion(BaseIngestion):
    """
    AWS CloudTrail ingestion for BuffaLogs.
    Fetches logs from S3, parses CloudTrail events, and normalizes them.
    """

    def __init__(self, config, s3_client=None):

        # tests expect this EXACT name
        mapping = config.get("custom_mapping", {})

        # BaseIngestion needs (config, mapping)
        super().__init__(config, mapping)

        # allow mock S3 client
        if s3_client:
            self.s3 = s3_client
        else:
            region = config.get("region") or "us-east-1"
            self.s3 = boto3.client(
                "s3",
                aws_access_key_id=config.get("aws_access_key_id"),
                aws_secret_access_key=config.get("aws_secret_access_key"),
                region_name=region
            )

        self.bucket = config.get("bucket_name", "")
        self.prefix = config.get("prefix", "")
        self.mapping = mapping

    def fetch(self):
        response = self.s3.list_objects_v2(
            Bucket=self.bucket,
            Prefix=self.prefix
        )
        return response.get("Contents", [])

    def parse(self, file_obj):
        """Download, decompress and parse CloudTrail data."""
        obj = self.s3.get_object(
            Bucket=self.bucket,
            Key=file_obj["Key"]
        )
        raw = obj["Body"].read()

        try:
            raw = gzip.decompress(raw)
        except OSError:
            pass

        data = json.loads(raw)
        return data.get("Records", [])

    def normalize(self, event):
        """Mapping fields based on config."""
        normalized = {}

        for cloud_key, ecs_key in self.mapping.items():
            value = self._extract(event, cloud_key)
            normalized[ecs_key] = value

        return normalized

    def _extract(self, obj, path):
        parts = path.split(".")
        for p in parts:
            if not isinstance(obj, dict) or p not in obj:
                return None
            obj = obj[p]
        return obj

    # abstract methods required by BaseIngestion
    def process_users(self, events):
        return []

    def process_user_logins(self, events):
        return []
