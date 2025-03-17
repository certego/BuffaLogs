## Overview

*Webhooks Alerting* is a mechanism for sending alert notifications via **webhooks**, using JWT tokens for authentication. It extends `HTTPRequestAlerting` and requires a **secret key** for generating secure tokens. The configuration is managed through `alerting.json`.

## Setup

To enable alert notifications via **webhooks**, configure `alerting.json` as follows:

```json
{
    "active_alerter": "webhooks",
    "webhooks": {
        "name": "",
        "endpoint": "",
        "secret_key_variable_name": "",
        "options": {
            "issuer": "",
            "token_expiration_seconds": "",
            "algorithm": "",
            "alert_types": [],
            "fields": [],
            "login_data": [],
            "batch_size": -1
        }
    }
}
```

### Configuration Parameters

- **active_alerter**: Specifies the notification method to use. Set it to `webhooks`.
- **webhooks**: Defines the *Webhooks Alerting* object.
- **name**: A reference name for the webhook service.
- **endpoint**: The URL where the webhook requests will be sent.
- **secret_key_variable_name**: Specifies the environment variable that holds the secret key for signing JWT tokens.
- **options**: Contains optional settings to customize request behavior and data sent.
  - **issuer**: Defines the issuer of the JWT token. Default: `buffalogs_webhook`.
  - **token_expiration_seconds**: Specifies how long the token remains valid (in seconds). Default: `300` (5 minutes).
  - **algorithm**: The algorithm used for signing JWT tokens. Default: `HS256`. Supported algorithms: `WEBHOOKS_ALGORITHM_LIST` (contains all supported algorithms in `Pyjwt`).
  - **alert_types**: A list of alert types to be sent. By default, all *Buffalogs* alert types are included.
  - **fields**: Defines the fields to include in the request payload. Available fields:
    ```
    ["name", "user", "created", "description", "is_vip", "is_filtered", "filter_type"]
    ```
    Default fields: `name, user, created, description`. The following special values are also accepted:
    - `_all_`: Includes all permitted fields.
    - `_empty_`: Excludes all fields.
  - **login_data**: Specifies fields to include from `Alert.login_data_raw`. Available fields:
    ```
    ["index", "lat", "lon", "country", "timestamp"]
    ```
    Default: all permitted fields. Also accepts `_all_` (include all) and `_empty_` (exclude all).
  - **batch_size** *(optional)*: Sends serialized alert objects in batches instead of one at a time. Default: `-1` (all alerts in a single request).

> **Note:** `name`, `endpoint`, and `secret_key_variable_name` are required. If any are missing, *Webhooks Alerting* will fail to initialize.

## Sample JSON Request

Given the following configuration:

```json
"webhooks": {
    "name": "service",
    "endpoint": "http://127.0.0.1:8000",
    "secret_key_variable_name": "WEBHOOK_SECRET",
    "options": {
        "issuer": "buffalogs_webhook",
        "token_expiration_seconds": 300,
        "algorithm": "HS256",
        "alert_types": ["Imp Travel", "New Device", "New Country"],
        "fields": ["name", "user"],  
        "login_data": ["lat", "lon"]
    }
}
```

The request sent to `http://127.0.0.1:8000` will contain:

```json
[
    {
        "name": "Imp Travel",
        "user": "test user's username",
        "lat": 56.0,
        "lon": 7.2
    },
    {...}
]
```

