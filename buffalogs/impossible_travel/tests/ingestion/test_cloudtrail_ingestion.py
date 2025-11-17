import json
import gzip
from unittest.mock import MagicMock
from impossible_travel.ingestion.cloudtrail_ingestion import CloudTrailIngestion


def test_cloudtrail_parsing_gzipped():
    """
    Test CloudTrail ingestion correctly parses gzipped CloudTrail records.
    """

    sample_event = {
        "Records": [
            {
                "eventTime": "2024-01-01T12:00:00Z",
                "sourceIPAddress": "1.2.3.4",
                "eventName": "ConsoleLogin",
                "userIdentity": {"userName": "test-user"},
                "awsRegion": "us-east-1"
            }
        ]
    }

    compressed = gzip.compress(json.dumps(sample_event).encode())

    # mock S3 client
    mock_s3 = MagicMock()
    mock_s3.get_object.return_value = {"Body": MagicMock(read=lambda: compressed)}

    config = {
        "aws_access_key_id": "",
        "aws_secret_access_key": "",
        "region": "",
        "bucket_name": "",
        "prefix": "",
        "custom_mapping": {
            "eventTime": "timestamp",
            "sourceIPAddress": "ip",
            "eventName": "event_name",
            "userIdentity.userName": "username",
            "awsRegion": "region"
        }
    }

    ingestion = CloudTrailIngestion(config)
    ingestion.s3 = mock_s3  # replace actual AWS S3 client

    result = ingestion.parse({"Key": "test.gz"})
    assert len(result) == 1
    assert result[0]["eventName"] == "ConsoleLogin"


def test_cloudtrail_normalize():
    """
    Test field normalization using the custom mapping.
    """

    event = {
        "eventTime": "2024-01-01T12:00:00Z",
        "sourceIPAddress": "5.6.7.8",
        "eventName": "AssumeRole",
        "userIdentity": {"userName": "alice"},
        "awsRegion": "eu-west-1"
    }

    config = {
        "custom_mapping": {
            "eventTime": "timestamp",
            "sourceIPAddress": "ip",
            "eventName": "event_name",
            "userIdentity.userName": "username",
            "awsRegion": "region"
        }
    }

    ingestion = CloudTrailIngestion(config)

    normalized = ingestion.normalize(event)

    assert normalized["timestamp"] == "2024-01-01T12:00:00Z"
    assert normalized["ip"] == "5.6.7.8"
    assert normalized["event_name"] == "AssumeRole"
    assert normalized["username"] == "alice"
    assert normalized["region"] == "eu-west-1"
