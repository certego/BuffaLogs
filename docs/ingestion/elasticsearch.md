# Connecting BuffaLogs to an Existing Elasticsearch Cluster

This guide explains how to configure BuffaLogs to work with an existing Elasticsearch cluster, including authentication, TLS/SSL settings, and index configuration.

## Table of Contents

- [Overview](#overview)
- [Configuration File](#configuration-file)
- [Connection Settings](#connection-settings)
- [Authentication](#authentication)
- [TLS/SSL Configuration](#tlsssl-configuration)
- [Index Configuration](#index-configuration)
- [Custom Field Mapping](#custom-field-mapping)
- [Docker Compose Examples](#docker-compose-examples)
- [Troubleshooting](#troubleshooting)

## Overview

BuffaLogs uses Elasticsearch as one of its supported ingestion sources for analyzing authentication logs. If you already have an Elasticsearch cluster running, you can configure BuffaLogs to connect to it instead of deploying a new instance.

## Configuration File

The main configuration for Elasticsearch is done in the `config/buffalogs/ingestion.json` file. This file controls:

- Which ingestion source is active (Elasticsearch, OpenSearch, or Splunk)
- Connection parameters (URL, credentials, timeout)
- Which indexes to query
- Field mappings between your log format and BuffaLogs' expected format

### Basic Configuration Structure

```json
{
    "active_ingestion": "elasticsearch",
    "elasticsearch": {
        "url": "http://elasticsearch:9200/",
        "username": "your_username",
        "password": "your_password",
        "timeout": 90,
        "indexes": "your-index-pattern-*",
        "bucket_size": 10000,
        "custom_mapping": { ... }
    }
}
```

## Connection Settings

### URL Configuration

The `url` parameter specifies your Elasticsearch cluster endpoint:

```json
{
    "elasticsearch": {
        "url": "http://your-elasticsearch-host:9200/"
    }
}
```

**Examples:**

| Scenario | URL Example |
|----------|-------------|
| Local development | `http://localhost:9200/` |
| Docker internal network | `http://elasticsearch:9200/` |
| Remote cluster (HTTP) | `http://es.example.com:9200/` |
| Remote cluster (HTTPS) | `https://es.example.com:9200/` |
| Elastic Cloud | `https://my-cluster.es.us-east-1.aws.cloud.es.io:9243/` |

### Timeout Configuration

The `timeout` parameter (in seconds) controls how long BuffaLogs will wait for Elasticsearch responses:

```json
{
    "elasticsearch": {
        "timeout": 90
    }
}
```

For large clusters or high-latency connections, consider increasing this value.

## Authentication

### Basic Authentication

Configure username and password for clusters with basic authentication enabled:

```json
{
    "elasticsearch": {
        "url": "https://your-elasticsearch-host:9200/",
        "username": "elastic",
        "password": "your_secure_password"
    }
}
```

### Security Best Practices

1. **Never commit credentials** to version control
2. **Use environment variables** where possible (see Docker Compose examples below)
3. **Create a dedicated user** for BuffaLogs with minimal required permissions:

   ```json
   {
       "cluster": ["monitor"],
       "indices": [
           {
               "names": ["your-index-pattern-*"],
               "privileges": ["read", "view_index_metadata"]
           }
       ]
   }
   ```

## TLS/SSL Configuration

### Current Behavior

By default, BuffaLogs disables TLS certificate verification when connecting to Elasticsearch. This is configured in the `elasticsearch_ingestion.py` file:

```python
connections.create_connection(
    hosts=self.ingestion_config["url"],
    request_timeout=self.ingestion_config["timeout"],
    verify_certs=False  # Certificate verification disabled
)
```

### Connecting to Secured Clusters

For **production environments with HTTPS**, you have several options:

#### Option 1: Use HTTPS with Verification Disabled (Development Only)

This is the default behavior. Simply use `https://` in your URL:

```json
{
    "elasticsearch": {
        "url": "https://your-elasticsearch-host:9200/"
    }
}
```

> ⚠️ **Warning**: Disabling certificate verification is not recommended for production as it makes the connection vulnerable to man-in-the-middle attacks.

#### Option 2: Trust a Custom CA Certificate

If your Elasticsearch cluster uses a certificate signed by a private Certificate Authority:

1. Mount the CA certificate into the BuffaLogs container
2. Set the `SSL_CERT_FILE` or `REQUESTS_CA_BUNDLE` environment variable

Example in `docker-compose.yaml`:

```yaml
services:
  buffalogs:
    environment:
      - SSL_CERT_FILE=/certs/ca.crt
    volumes:
      - ./certs/ca.crt:/certs/ca.crt:ro
```

#### Option 3: Enable Full Certificate Verification

For production environments, modify the Elasticsearch ingestion code to enable verification:

1. Edit `buffalogs/impossible_travel/ingestion/elasticsearch_ingestion.py`
2. Change `verify_certs=False` to `verify_certs=True`
3. Optionally specify the CA certificate path

## Index Configuration

### Specifying Indexes

The `indexes` parameter accepts comma-separated index patterns:

```json
{
    "elasticsearch": {
        "indexes": "cloud-*,fw-proxy-*"
    }
}
```

### Index Pattern Examples

| Use Case | Pattern Example |
|----------|-----------------|
| Single index | `authentication-logs` |
| Wildcard pattern | `auth-*` |
| Multiple patterns | `cloud-*,fw-proxy-*,sso-*` |
| Date-based indices | `logs-auth-*` |
| Data streams | `.ds-logs-*` |

### Required Log Format

BuffaLogs expects authentication logs to follow the [Elastic Common Schema (ECS)](https://www.elastic.co/guide/en/ecs/current/index.html) format. Specifically, it queries for:

- `event.category: authentication`
- `event.outcome: success`
- `event.type: start`

If your logs use a different schema, use the `custom_mapping` configuration to map your fields to the expected format.

## Custom Field Mapping

The `custom_mapping` section maps your log fields to BuffaLogs' internal field names:

```json
{
    "elasticsearch": {
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
            "source.intelligence_category": "intelligence_category"
        }
    }
}
```

### Mapping Reference

| BuffaLogs Field | Description | Required |
|-----------------|-------------|----------|
| `timestamp` | Event timestamp | ✅ Yes |
| `id` | Unique event identifier | ✅ Yes |
| `index` | Source index name | ✅ Yes |
| `username` | Authenticated user's name | ✅ Yes |
| `ip` | Source IP address | ✅ Yes |
| `agent` | User agent string | No |
| `organization` | AS organization name | No |
| `country` | Geographic country | No |
| `lat` | Geographic latitude | No |
| `lon` | Geographic longitude | No |
| `intelligence_category` | Threat intelligence category | No |

## Docker Compose Examples

### Connecting to an External Elasticsearch Cluster

```yaml
# docker-compose.override.yaml
services:
  buffalogs:
    volumes:
      - ./config/buffalogs:/etc/buffalogs:rw
    environment:
      - CERTEGO_BUFFALOGS_CONFIG_PATH=/etc/
```

Update `config/buffalogs/ingestion.json`:

```json
{
    "active_ingestion": "elasticsearch",
    "elasticsearch": {
        "url": "https://your-external-cluster:9200/",
        "username": "buffalogs_user",
        "password": "secure_password_here",
        "timeout": 90,
        "indexes": "authentication-*",
        "bucket_size": 10000,
        "custom_mapping": { ... }
    }
}
```

### Using Environment Variables for Credentials

While the current implementation reads directly from `ingestion.json`, you can use Docker secrets or environment variable substitution in your deployment scripts:

```bash
# Replace placeholders before starting
sed -i "s/ELASTIC_USER/${ELASTICSEARCH_USER}/g" config/buffalogs/ingestion.json
sed -i "s/ELASTIC_PASS/${ELASTICSEARCH_PASSWORD}/g" config/buffalogs/ingestion.json

docker compose up -d
```

### Running Commands

```bash
# Start BuffaLogs with an existing Elasticsearch cluster
docker compose up -d

# Or with the included Elasticsearch for testing
docker compose -f docker-compose.yaml -f docker-compose.elastic.yaml up -d
```

## Troubleshooting

### Connection Issues

#### Failed to establish a connection

1. Verify the Elasticsearch URL is accessible from the BuffaLogs container:

   ```bash
   docker exec buffalogs curl -v http://your-elasticsearch:9200/
   ```

2. Check network connectivity and firewall rules
3. Ensure the Elasticsearch container/service is running

#### Connection timeout

1. Increase the `timeout` value in `ingestion.json`
2. Check network latency to the Elasticsearch cluster
3. Verify cluster health: `GET /_cluster/health`

### Authentication Issues

#### Authentication failed

1. Verify username and password are correct
2. Check user permissions in Elasticsearch
3. For Elastic Cloud, use the Cloud ID or correct endpoint URL

### No Data Returned

1. Verify the index patterns match existing indices:

   ```bash
   GET /_cat/indices?v&index=your-pattern-*
   ```

2. Check that your logs match the expected query format (ECS schema)
3. Verify the custom mapping matches your log fields
4. Check BuffaLogs logs for query errors:

   ```bash
   docker logs buffalogs 2>&1 | grep -i elastic
   ```

### SSL/TLS Issues

#### SSL certificate verification failed

1. If using self-signed certificates, ensure `verify_certs=False` is set (default)
2. For production, configure proper CA certificates
3. Check that the certificate's CN matches the hostname

## Additional Resources

- [Elasticsearch Security Documentation](https://www.elastic.co/guide/en/elasticsearch/reference/current/secure-cluster.html)
- [Elastic Common Schema (ECS)](https://www.elastic.co/guide/en/ecs/current/index.html)
- [BuffaLogs Troubleshooting Guide](../troubleshooting.md)
