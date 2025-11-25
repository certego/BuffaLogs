"""
CloudTrail ingestion for Impossible Travel (ConsoleLogin only)
"""

import gzip
import io
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set

import boto3
from botocore.exceptions import ClientError

from .base_ingestion import BaseIngestion


class CloudTrailIngestion(BaseIngestion):
    """
    CloudTrail ingestion compatible with Impossible Travel.

    Expected ingestion_config keys:
    - bucket_name (required)
    - prefix (optional)
    - region (optional)
    """

    def __init__(self, ingestion_config: Dict, mapping: Dict):
        super().__init__(ingestion_config, mapping)

        self.bucket = ingestion_config.get("bucket_name")
        if not self.bucket:
            raise ValueError("cloudtrail ingestion: 'bucket_name' is required")

        self.prefix = ingestion_config.get("prefix", "")
        self.region = ingestion_config.get("region")

        self.s3 = None

    def _ensure_s3(self):
        if self.s3 is None:
            if self.region:
                session = boto3.Session(region_name=self.region)
            else:
                session = boto3.Session()
            self.s3 = session.client("s3")

    def _parse_iso(self, t: Optional[str]) -> Optional[datetime]:
        if not t:
            return None
        try:
            return datetime.strptime(
                t,
                "%Y-%m-%dT%H:%M:%SZ",
            ).replace(tzinfo=timezone.utc)
        except Exception:
            try:
                return datetime.fromisoformat(t)
            except Exception:
                return None

    def _iter_objects(self):
        self._ensure_s3()
        paginator = self.s3.get_paginator("list_objects_v2")
        try:
            for page in paginator.paginate(
                Bucket=self.bucket,
                Prefix=self.prefix,
            ):
                for obj in page.get("Contents", []) or []:
                    yield obj.get("Key")
        except ClientError as e:
            self.logger.exception(
                "cloudtrail: error listing objects: %s",
                e,
            )

    def _read_gz_json(self, key: str) -> Optional[Dict]:
        self._ensure_s3()
        try:
            resp = self.s3.get_object(
                Bucket=self.bucket,
                Key=key,
            )
            data = resp["Body"].read()
            with gzip.GzipFile(fileobj=io.BytesIO(data)) as gz:
                payload = gz.read().decode("utf-8")
            return json.loads(payload)
        except Exception:
            self.logger.warning(
                "cloudtrail: failed to parse %s",
                key,
            )
            return None

    def process_users(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> List[str]:
        users: Set[str] = set()
        start_dt = start_date.astimezone(timezone.utc)
        end_dt = end_date.astimezone(timezone.utc)

        for key in self._iter_objects():
            if not key.endswith(".gz"):
                continue

            data = self._read_gz_json(key)
            if not data:
                continue

            for rec in data.get("Records", []) or []:
                if rec.get("eventName") != "ConsoleLogin":
                    continue

                evt_time = self._parse_iso(rec.get("eventTime"))
                if not evt_time:
                    continue

                if not (start_dt <= evt_time <= end_dt):
                    continue

                user = self._extract_username_from_record(rec)
                if user:
                    users.add(user)

        return list(users)

    def process_user_logins(
        self,
        start_date: datetime,
        end_date: datetime,
        username: str,
    ) -> List[Dict]:
        events: List[Dict] = []
        start_dt = start_date.astimezone(timezone.utc)
        end_dt = end_date.astimezone(timezone.utc)

        for key in self._iter_objects():
            if not key.endswith(".gz"):
                continue

            data = self._read_gz_json(key)
            if not data:
                continue

            for rec in data.get("Records", []) or []:
                if rec.get("eventName") != "ConsoleLogin":
                    continue

                evt_time = self._parse_iso(rec.get("eventTime"))
                if not evt_time:
                    continue

                if not (start_dt <= evt_time <= end_dt):
                    continue

                user = self._extract_username_from_record(rec)
                if not user or user != username:
                    continue

                login = {
                    "@timestamp": rec.get("eventTime"),
                    "user": {"name": user},
                    "source": {
                        "ip": rec.get("sourceIPAddress"),
                        "geo": {
                            "country_name": "",
                            "location": {
                                "lat": "",
                                "lon": "",
                            },
                        },
                        "as": {"organization": ""},
                    },
                    "user_agent": {"original": rec.get("userAgent")},
                    "raw_event": rec,
                }

                events.append(login)

        return events

    def _extract_username_from_record(
        self,
        rec: Dict,
    ) -> Optional[str]:
        user = rec.get("userIdentity") or {}
        if not isinstance(user, dict):
            return None

        if user.get("userName"):
            return user.get("userName")

        session_ctx = user.get("sessionContext", {})
        issuer = session_ctx.get("sessionIssuer", {})

        if issuer.get("userName"):
            return issuer.get("userName")

        return user.get("principalId")
