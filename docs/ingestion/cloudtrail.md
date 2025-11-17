# AWS CloudTrail Ingestion

## Overview

AWS CloudTrail provides detailed logs of activity within an AWS account.  
This ingestion source enables BuffaLogs to read CloudTrail logs stored in an Amazon S3 bucket, parse their events, and normalize them for use in the Impossible Travel detection engine.

CloudTrail logs include:

- Console logins
- API calls
- IAM role/user operations
- Security and configuration changes
- Region-level activity

CloudTrail integration makes BuffaLogs cloud-aware and extends its visibility into AWS environments.

---

## How It Works

1. CloudTrail delivers log files (`.json` or `.json.gz`) to an S3 bucket.
2. BuffaLogs connects to AWS using the Boto3 SDK.
3. The ingestion engine lists all S3 objects under the configured prefix.
4. Each log file is downloaded and parsed.
5. Events inside the `Records[]` array are normalized using ECS-style fields.
6. Normalized events are processed by Impossible Travel and other detection modules.

---

## Configuration

Add the following block to:

```json
"cloudtrail": {
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
  },
  "__custom_fields__": [
    "aws_access_key_id",
    "aws_secret_access_key",
    "region",
    "bucket_name",
    "prefix"
  ]
}
```

To enable CloudTrail ingestion, set:

```json
"active_ingestion": "cloudtrail"
```

## Field Mapping

| CloudTrail Field      | BuffaLogs Field |
| --------------------- | --------------- |
| eventTime             | timestamp       |
| sourceIPAddress       | ip              |
| eventName             | event_name      |
| userIdentity.userName | username        |
| awsRegion             | region          |

Mappings are fully customizable using the `custom_mapping` section.

## Implementation Reference

Source implementation:

```
buffalogs/impossible_travel/ingestion/cloudtrail_ingestion.py
```

This implementation follows the structure of:

- `elasticsearch_ingestion.py`

- `splunk_ingestion.py`

- `opensearch_ingestion.py`

## Screenshots

Add screenshots once CloudTrail ingestion is configured in your environment.

Examples you can include later:

- Example CloudTrail JSON event
- BuffaLogs ingestion logs
- Impossible Travel alerts generated from CloudTrail events
