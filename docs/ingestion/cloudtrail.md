# CloudTrail Ingestion

This document describes the CloudTrail ingestion source added to BuffaLogs as part of Issue #228.

## Overview

AWS CloudTrail provides logs of account activity, including ConsoleLogin events.  
This ingestion source allows BuffaLogs to detect cloud login anomalies from CloudTrail S3 buckets.

## Configuration

Add the following block in `config/buffalogs/ingestion.json`:

```json
"cloudtrail": {
  "type": "cloudtrail",
  "bucket_name": "<your-bucket>",
  "prefix": "AWSLogs/",
  "region": "us-east-1"
}
```
