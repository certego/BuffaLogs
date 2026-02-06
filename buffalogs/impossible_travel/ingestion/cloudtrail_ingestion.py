import gzip
import json
import logging
from datetime import datetime, timedelta

import boto3
import geoip2.database
from dateutil import parser
from geoip2.errors import AddressNotFoundError
from impossible_travel.ingestion.base_ingestion import BaseIngestion


class CloudTrailIngestion(BaseIngestion):
    """
    Concrete implementation of the BaseIngestion class for AWS CloudTrail
    ingestion source
    """

    def __init__(self, ingestion_config: dict, mapping: dict):
        """
        Constructor for the CloudTrail Ingestion object
        """
        super().__init__(ingestion_config, mapping)
        self.s3 = boto3.client(
            "s3",
            aws_access_key_id=ingestion_config.get("aws_access_key_id"),
            aws_secret_access_key=ingestion_config.get("aws_secret_access_key"),
            region_name=ingestion_config["region"],
        )
        self.bucket = ingestion_config["bucket_name"]
        self.prefix_template = ingestion_config.get("prefix_template", "AWSLogs/{account_id}/CloudTrail/{region}/")  # User can override
        self.geo_db_path = ingestion_config.get("geo_db_path", "/etc/buffalogs/GeoLite2-City.mmdb")
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        try:
            self.geo_reader = geoip2.database.Reader(self.geo_db_path)
        except FileNotFoundError:
            msg = f"GeoIP database not found at {self.geo_db_path}. " "Geo-enrichment disabled."
            self.logger.warning(msg)
            self.geo_reader = None

    def get_log_files(self, start_date: datetime, end_date: datetime) -> list:
        """
        Get list of S3 keys for CloudTrail logs in the time range.
        Assumes standard CloudTrail prefix structure.
        Handles pagination for list_objects_v2.
        """
        files = []
        current = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        account_id = self.ingestion_config.get("account_id", "")
        region = self.ingestion_config["region"]  # Required in config

        while current < end_date:
            date_part = f"{current.year}/{current.month:02d}/{current.day:02d}/"  # noqa: E501
            prefix = self.prefix_template.format(account_id=account_id, region=region) + date_part

            try:
                paginator = self.s3.get_paginator("list_objects_v2")
                for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix):
                    for obj in page.get("Contents", []):
                        files.append(obj["Key"])
            except Exception as e:
                err_msg = f"Error listing S3 objects for prefix " f"{prefix}: {e}"
                self.logger.error(err_msg)
            current += timedelta(days=1)
        return files

    def extract_logins(self, files: list) -> list:
        """
        Extract and parse login events from S3 files.
        """
        logins = []
        for key in files:
            try:
                obj = self.s3.get_object(Bucket=self.bucket, Key=key)
                with gzip.GzipFile(fileobj=obj["Body"]) as f:
                    data = json.load(f)
                    for record in data.get("Records", []):
                        if self.is_login_event(record):
                            login = self.parse_login(record)
                            if login:
                                logins.append(login)
            except Exception as e:
                self.logger.error(f"Error processing S3 file {key}: {e}")
        return logins

    def is_login_event(self, record: dict) -> bool:
        """
        Filter for relevant security/login events.
        Equivalent to ES filters: authentication, success, start.
        """
        if record.get("errorCode") is not None or record.get("errorMessage") is not None:
            return False  # Only successful events

        event_name = record.get("eventName")
        event_source = record.get("eventSource")

        # Console sign-ins
        if event_source == "signin.amazonaws.com" and event_name in ["ConsoleLogin", "CheckMfa"]:
            return True

        # Role assumptions (like starting a session)
        if event_name in [
            "AssumeRole",
            "AssumeRoleWithSAML",
            "AssumeRoleWithWebIdentity",
            "GetSessionToken",
        ]:
            return True

        # Add more if needed, e.g., 'SwitchRole'
        return False

    def parse_login(self, record: dict) -> dict | None:
        """
        Parse and enrich a single CloudTrail event into a format similar to ES hits.  # noqa: E501
        Keys match the mapping (e.g., '@timestamp', 'user.name', etc.).
        """
        data = {}
        data["@timestamp"] = record.get("eventTime", "")

        user_identity = record.get("userIdentity", {})
        session_issuer = user_identity.get("sessionContext", {}).get("sessionIssuer", {})

        arn_last = user_identity.get("arn", "").split("/")[-1]
        principal_last = user_identity.get("principalId", "").split(":")[-1]

        data["user.name"] = user_identity.get("userName") or session_issuer.get("userName") or arn_last or principal_last or ""

        data["source.ip"] = record.get("sourceIPAddress", "")
        data["user_agent.original"] = record.get("userAgent", "")
        data["source.as.organization.name"] = ""  # Not available in CloudTrail; can enrich externally if needed

        ip = data["source.ip"]
        if not ip or ip == "127.0.0.1" or ip.startswith(("10.", "192.168.", "172.16.")):
            return None  # Skip invalid/local IPs

        # Geo-enrichment
        data["source.geo.country_name"] = ""
        data["source.geo.location.lat"] = ""
        data["source.geo.location.lon"] = ""

        if self.geo_reader:
            try:
                geo = self.geo_reader.city(ip)
                data["source.geo.country_name"] = geo.country.name or ""
                data["source.geo.location.lat"] = geo.location.latitude or ""
                data["source.geo.location.lon"] = geo.location.longitude or ""
            except AddressNotFoundError:
                self.logger.debug(f"GeoIP not found for IP: {ip}")
            except Exception as e:
                self.logger.error(f"GeoIP error for IP {ip}: {e}")

        if not data["source.geo.country_name"]:  # Skip if no geo
            return None

        # Intelligence category (e.g., anonymous)
        ua_lower = data["user_agent.original"].lower()
        is_anonymous = user_identity.get("type") == "AnonymousUser" or "tor" in ua_lower
        data["source.intelligence_category"] = "anonymous" if is_anonymous else ""  # noqa: E501

        # Other fields
        data["_id"] = record.get("eventID", "")
        data["_index"] = "cloudtrail"
        return data

    def process_users(self, start_date: datetime, end_date: datetime) -> list:
        """
        Concrete implementation of the BaseIngestion.process_users abstract method  # noqa: E501
        """
        msg = f"Processing users from {start_date} to {end_date}"
        self.logger.info(msg)

        files = self.get_log_files(start_date, end_date)
        logins = self.extract_logins(files)

        users = set()
        for login in logins:
            name = login.get("user.name")
            if name:
                users.add(name)
        return list(users)

    def process_user_logins(self, start_date: datetime, end_date: datetime, username: str) -> list:
        """
        Concrete implementation of the BaseIngestion.process_user_logins
        abstract method
        """
        msg = f"Processing logins for user {username} " f"from {start_date} to {end_date}"
        self.logger.info(msg)

        files = self.get_log_files(start_date, end_date)
        logins = self.extract_logins(files)

        user_logins = []
        for login in logins:
            if login.get("user.name") == username:
                user_logins.append(login)

        # Sort by timestamp, similar to ES sort
        user_logins.sort(key=lambda x: parser.parse(x["@timestamp"]))
        return user_logins
