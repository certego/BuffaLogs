import gzip
import json
from datetime import datetime, timezone
from unittest.mock import patch

import boto3
from impossible_travel.ingestion.cloudtrail_ingestion import CloudTrailIngestion
from moto import mock_aws


@mock_aws
def test_integration():
    # Setup config (mimics ingestion.json)
    config = {
        "bucket_name": "test-bucket",
        "region": "us-east-1",
        "account_id": "123456789012",
        "prefix_template": "AWSLogs/{account_id}/CloudTrail/{region}/",
        "geo_db_path": "/fake/path.mmdb",  # Fake path - we force geo success
        "timeout": 90,
        "bucket_size": 10000,
        "custom_mapping": {
            "@timestamp": "timestamp",
            "_id": "id",
            "_index": "index",
            "user.name": "username",
            "source.ip": "ip",
            "user_agent.original": "agent",
            "source.as.organization.name": "organization",
            "source.geo.country_name": "country",
            "source.geo.location.lat": "lat",
            "source.geo.location.lon": "lon",
            "source.intelligence_category": "intelligence_category",
        },
    }

    # Create mock S3 bucket
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket="test-bucket")

    # Mock CloudTrail log file
    mock_record_alice = {
        "eventTime": "2025-10-15T10:00:00Z",
        "eventSource": "signin.amazonaws.com",
        "eventName": "ConsoleLogin",
        "userIdentity": {"userName": "alice"},
        "sourceIPAddress": "203.0.113.55",
        "userAgent": "Mozilla/5.0",
        "errorCode": None,
    }
    mock_record_bob = {
        "eventTime": "2025-10-15T12:00:00Z",
        "eventSource": "sts.amazonaws.com",
        "eventName": "AssumeRole",
        "userIdentity": {
            "type": "AssumedRole",
            "sessionContext": {"sessionIssuer": {"userName": "bob"}},
        },
        "sourceIPAddress": "198.51.100.77",
        "userAgent": "Mozilla/5.0",
        "errorCode": None,
    }
    mock_log = {"Records": [mock_record_alice, mock_record_bob]}
    gz_log = gzip.compress(json.dumps(mock_log).encode())
    s3.put_object(
        Bucket="test-bucket",
        Key=("AWSLogs/123456789012/CloudTrail/us-east-1/" "2025/10/15/file.json.gz"),
        Body=gz_log,
    )

    # Create ingestion instance
    ingestion = CloudTrailIngestion(config, config["custom_mapping"])

    # Mock parse_login to force success (no recursion, full implementation)
    def mock_parse_login(self, record):
        data = {
            "@timestamp": record.get("eventTime", ""),
            "user.name": (
                record.get("userIdentity", {}).get("userName")
                or record.get("userIdentity", {}).get("sessionContext", {}).get("sessionIssuer", {}).get("userName")
                or ""
            ),
            "source.ip": record.get("sourceIPAddress", ""),
            "user_agent.original": record.get("userAgent", ""),
            "source.as.organization.name": "",
            "source.geo.country_name": "MockCountry",
            "source.geo.location.lat": 0.0,
            "source.geo.location.lon": 0.0,
            "source.intelligence_category": "",
            "_id": record.get("eventID", ""),
            "_index": "cloudtrail",
        }

        # Skip invalid IPs
        ip = data["source.ip"]
        if not ip or ip == "127.0.0.1" or ip.startswith(("10.", "192.168.", "172.16.")):
            return None

        # Skip if no country (but we force it here)
        if not data["source.geo.country_name"]:
            return None

        return data

    with patch.object(CloudTrailIngestion, "parse_login", mock_parse_login):
        # Test process_users
        users = ingestion.process_users(
            start_date=datetime(2025, 10, 15, tzinfo=timezone.utc),
            end_date=datetime(2025, 10, 16, tzinfo=timezone.utc),
        )
        print("Users found:", users)
        assert sorted(users) == ["alice", "bob"], "process_users failed"

        # Test process_user_logins
        alice_logins = ingestion.process_user_logins(
            start_date=datetime(2025, 10, 15, tzinfo=timezone.utc),
            end_date=datetime(2025, 10, 16, tzinfo=timezone.utc),
            username="alice",
        )
        print("Alice logins:", alice_logins)
        assert len(alice_logins) == 1, "process_user_logins failed for alice"
        assert alice_logins[0]["user.name"] == "alice", "Wrong username"
        assert alice_logins[0]["source.ip"] == "203.0.113.55", "Wrong IP"

    print("Integration test PASSED!")
    return "SUCCESS"


if __name__ == "__main__":
    result = test_integration()
    print(result)
