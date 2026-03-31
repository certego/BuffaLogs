```markdown
# AWS CloudTrail Ingestion

BuffaLogs now supports ingesting login-related events directly from **AWS CloudTrail** logs stored in an S3 bucket.  
This enables detection of impossible travel, anomalous logins from new countries or IPs, root activity, anonymous access attempts, role assumption abuse, and other suspicious identity behavior in AWS environments.

## Why CloudTrail?

- Captures console sign-ins (`ConsoleLogin`), role assumptions (`AssumeRole`, `AssumeRoleWithSAML`, `AssumeRoleWithWebIdentity`), temporary credentials (`GetSessionToken`), and more.
- Fills a major gap for cloud-native environments — current sources are mostly on-prem (SSH, Apache) or specific IdPs.
- Combined with GeoIP enrichment, it allows full impossible travel and anomaly detection in AWS accounts.

## Prerequisites

1. **CloudTrail must be enabled and logging to S3**  
   - Create a **trail** (preferably multi-region)  
   - Enable **management events** (and optionally global service events)  
   - Choose an S3 bucket to store the logs

2. **IAM permissions**  
   - `s3:ListBucket` + `s3:GetObject` on the CloudTrail bucket  
   - Best practice: Use an **IAM role** (if BuffaLogs runs in AWS/EC2/Lambda/Fargate) instead of long-lived access keys

3. **GeoLite2 City database for IP → country/lat/lon enrichment**  
   - Free download: https://www.maxmind.com/en/accounts/current/geoip/downloads (requires free account signup)  
   - File: `GeoLite2-City.mmdb`  
   - Recommended location: `/etc/buffalogs/GeoLite2-City.mmdb` (or any path you specify in config)

## Configuration

Edit `config/buffalogs/ingestion.json` and add/replace with:

```json
{
    "active_ingestion": "cloudtrail",
    "cloudtrail": {
        "bucket_name": "your-cloudtrail-logs-bucket-name",
        "region": "us-east-1",
        "account_id": "123456789012",
        "aws_access_key_id": "AKIAXXXXXXXXXXXXXXXX",          // optional — remove if using IAM role / env vars
        "aws_secret_access_key": "your-secret-key-here",      // optional — remove if using IAM role / env vars
        "prefix_template": "AWSLogs/{account_id}/CloudTrail/{region}/",
        "geo_db_path": "/etc/buffalogs/GeoLite2-City.mmdb",
        "timeout": 90,
        "bucket_size": 10000
    }
}
```

### Docker Compose volume example (for GeoLite2 DB)

```yaml
services:
  buffalogs:
    volumes:
      - ./GeoLite2-City.mmdb:/etc/buffalogs/GeoLite2-City.mmdb:ro
```

## How It Works

- Scans S3 day-by-day for the requested time range
- Downloads and decompresses `.json.gz` files
- Filters only **successful** login/identity events:
  - `ConsoleLogin` (main console sign-in)
  - `AssumeRole`, `AssumeRoleWithSAML`, `AssumeRoleWithWebIdentity`, `GetSessionToken`
- Enriches public source IPs with country + lat/lon using MaxMind GeoLite2
- Skips:
  - Failed events (have `errorCode`)
  - Internal AWS IPs / localhost / private ranges
  - Events without usable geo data
- Normalizes fields to match the format expected by impossible travel detection

## Testing & Verification

1. Set `"active_ingestion": "cloudtrail"` in `ingestion.json`
2. Restart services (`docker compose down && docker compose up -d`)
3. Trigger analysis (via UI or celery beat/task)
4. Check container logs for lines like:
   ```
   Processing users from 2025-10-01 to 2025-10-02
   Processing logins for user alice from ...
   ```
5. Look in the BuffaLogs dashboard for new anomalies (especially impossible travel between distant locations)

## Troubleshooting

| Issue                              | Possible Cause / Fix                                                                 |
|------------------------------------|---------------------------------------------------------------------------------------|
| No events ingested                 | CloudTrail not writing management events, wrong bucket/region/account_id, empty time range |
| Geo fields empty / anomalies missing | GeoLite2-City.mmdb missing, wrong path, or IP not found in database                   |
| S3 access denied                   | Wrong credentials, missing IAM permissions, or bucket policy blocking                |
| Slow ingestion on large ranges     | CloudTrail logs can be voluminous — test with 1–3 days first                          |
| "GeoIP database not found" warning | Mount the `.mmdb` file correctly or update `geo_db_path`                              |

## Security Recommendations

- **Never commit access keys** to git — use environment variables, AWS Secrets Manager, or IAM roles.
- Use least-privilege IAM policy.
- Consider enabling CloudTrail log file validation and S3 bucket encryption.

## Future Enhancements (ideas for follow-up PRs)

- Support for data events or CloudTrail Lake queries
- AS/ISP enrichment (requires paid MaxMind or external service)
- Caching / incremental ingestion
- Filtering specific event sources or users via config

Enjoy cloud threat hunting with BuffaLogs!

Feel free to open issues or contribute improvements.
```