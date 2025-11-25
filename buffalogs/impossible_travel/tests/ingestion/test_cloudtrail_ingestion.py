import gzip
import io
import json
from datetime import datetime, timezone

import boto3
from moto import mock_aws
from impossible_travel.ingestion.cloudtrail_ingestion import (
    CloudTrailIngestion,
)

# Sample CloudTrail ConsoleLogin record
SAMPLE_EVENT = {
    "Records": [
        {
            "eventVersion": "1.08",
            "userIdentity": {
                "type": "IAMUser",
                "principalId": "EXAMPLEID",
                "arn": "arn:aws:iam::123456789012:user/Alice",
                "accountId": "123456789012",
                "userName": "Alice",
            },
            "eventTime": "2024-01-01T12:00:00Z",
            "eventSource": "signin.amazonaws.com",
            "eventName": "ConsoleLogin",
            "awsRegion": "us-east-1",
            "sourceIPAddress": "1.2.3.4",
            "userAgent": "signin.amazonaws.com",
        }
    ]
}


@mock_aws
def test_cloudtrail_ingestion_users_and_logins():
    # Arrange
    bucket = "test-cloudtrail"
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket=bucket)

    # Create gzipped JSON object
    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode="w") as gz:
        gz.write(json.dumps(SAMPLE_EVENT).encode("utf-8"))
    buf.seek(0)

    key = "AWSLogs/123456789012/CloudTrail/us-east-1/2024/01/01/example.gz"
    s3.put_object(Bucket=bucket, Key=key, Body=buf.read())

    ingestion_config = {
        "bucket_name": bucket,
        "prefix": "AWSLogs/",
        "region": "us-east-1",
    }

    # Empty mapping because CloudTrail already formats fields correctly
    mapping = {}

    ing = CloudTrailIngestion(ingestion_config, mapping)

    start = datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc)
    end = datetime(2024, 1, 2, 0, 0, tzinfo=timezone.utc)

    # Act
    users = ing.process_users(start, end)
    logins = ing.process_user_logins(start, end, "Alice")

    # Assert
    assert "Alice" in users
    assert len(logins) == 1

    event = logins[0]
    assert event["@timestamp"] == "2024-01-01T12:00:00Z"
    assert event["user"]["name"] == "Alice"
    assert event["source"]["ip"] == "1.2.3.4"
    assert event["user_agent"]["original"] == "signin.amazonaws.com"
