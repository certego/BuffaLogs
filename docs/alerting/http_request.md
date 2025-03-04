## Overview

*HTTP Request Alerting* is a mechanism for sending alert notifications via HTTP request to a designated listening service configured in `alerting.json`. It uses **bearer token authentication** to send a POST request containing a serialized `Alert` object. The fields included in the request can be customized through `alerting.json`.

## Setup

To enable alert notifications via **HTTP request**, configure `alerting.json` as follows:

```json
{
    "active_alerter": "http_request",
    "http_request": {
        "name": "",
        "endpoint": "",
        "options": {
            "token_variable_name": "",
            "alert_types": [],
            "fields": [],
            "login_data": []
        }
    }
}
```

### Configuration Parameters

- **active_alerter**: Specifies the notification method to use. Set it to `http_request`.
- **http_request**: Defines the *HTTP Request Alerting* object.
- **name**: A reference name for the listening service (e.g., `log_listener_service`). Any valid string can be used.
- **endpoint**: The URL where the POST request will be sent.
- **options**: Contains optional settings to customize request behavior and data sent.
  - **token_variable_name**: Used for bearer token authentication. The token should be stored as an environment variable, and this key specifies its lookup name in `os.environ`. If omitted, authentication is not used.
  - **alert_types**: A list of alert types to be sent. By default, all *Buffalogs* alert types are included. If an invalid alert type is provided, it will be skipped and logged.
  - **fields**: Defines the fields to include in the request payload. Available fields are:
    ```
    ["name", "user", "created", "description", "is_vip", "is_filtered", "filter_type"]
    ```
    Default fields: `name, user, created, description`. The following special values are also accepted:
    - `_all_`: Includes all permitted fields.
    - `_empty_`: Excludes all fields.
  - **login_data**: Specifies fields to include from `Alert.login_data_raw`. Available fields are:
    ```
    ["index", "lat", "lon", "country", "timestamp"]
    ```
    Default: all permitted fields. Also accepts `_all_` (include all) and `_empty_` (exclude all).
  - **batch_size** *(optional)*: Sends serialized alert objects in batches instead of all at a once.

> **Note:** `name` and `endpoint` are required. If either is missing, *HTTPRequestAlerting* will fail to initialize.

## Sample JSON Request

Given the following configuration:

```json
"http_request": {
    "name": "service",
    "endpoint": "http://127.0.0.1:8000",
    "options": {
        "token_variable_name": "TEST_TOKEN",
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

## Developer Guide

*HTTPRequestAlerting* can be extended for additional use cases. In most cases, modifying `send_notification` and defining additional class attributes is sufficient for integration with specific APIs or external services.

### Example Implementation

```python
class MyAlertingClass(HTTPRequest):
    required_fields = []
    extra_options = {"key_name": "default_value"}
    extra_option_parsers = {"key_name": parse_function}

    def send_notification(self, recipient_name: str, endpoint: str, data: list[dict]):
        ...
```

### Customization Options

- **required_fields**: Specifies mandatory keys in the configuration dictionary (excluding `options`).
- **extra_options**: Defines additional optional configuration settings beyond `alert_types`, `fields`, and `login_data`.
- **extra_option_parsers**: Maps option keys to parser functions, ensuring proper value validation.

### Example Parsing Function

```python
def parse_function(value):
    if value_passes_test:
        return None, value
    else:
        return "Error message", default_value_for_key
```

If an error message is returned, it will be logged. If additional arguments are needed, `functools.partial` can be used:

```python
from functools import partial

def parse_function(value, extra_arg, keyword_arg=None):
    # Perform parsing
    ...

class MyAlertingClass(HTTPRequestAlerting):
    extra_option_parsers = {"some_key": partial(parse_function, required_arg, keyword_arg=value)}
```

As long as `value` is the first argument, additional parameters can be predefined or optional.

