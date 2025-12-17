-----

# BuffaLogs REST APIs Overview

Five views were implemented using **DRF (Django-Rest Framework)** to provide data for dashboard charts and detailed queries.

| API Name | Purpose |
| :--- | :--- |
| `users_pie_chart_api` | Returns the **user count** for each **risk level**. |
| `alerts_line_chart_api` | Provides the **number of alerts** triggered over time in a specified period. |
| `world_map_chart_api` | Supplies the **geographic location (country, lat/lon)** and count of alerts. |
| `risk_score_api` | Provides the **user-to-risk level** association for users whose risk score changed. |
| `alerts_api` | Offers **detailed information** about generated alerts. |

-----

## Users Pie Chart API

This API retrieves the count of users grouped by their current risk score.

### Input Parameters (Query String)

| Parameter Name | Type | Description |
| :--- | :--- | :--- |
| `start` | `datetime` | Start datetime for filtering (captured in URL: `users_pie_chart_api/start=...`). |
| `end` | `datetime` | End datetime for filtering (captured in URL: `users_pie_chart_api/end=...`). |

### Expected Output (JSON Response)

A JSON object where **risk levels** are keys and the **number of users** assigned to that risk level are the values.

| JSON Key | Data Type | Description |
| :--- | :--- | :--- |
| Risk Level (e.g., `"No risk"`, `"Low"`, etc.) | `int` | The number of users with the corresponding risk score. |

### Example Output

```json
{
  "No risk": 32,
  "Low": 2,
  "Medium": 86,
  "High": 4
}
```

-----

## Alerts Line Chart API

This API provides the number of alerts triggered over a specified time period, aggregated by hour, day, or month based on the duration of the request.

### Input Parameters (Query String)

| Parameter Name | Type | Description |
| :--- | :--- | :--- |
| `start` | `datetime` | Start datetime for filtering (captured in URL: `alerts_line_chart_api/start=...`). |
| `end` | `datetime` | End datetime for filtering (captured in URL: `alerts_line_chart_api/end=...`). |

### Expected Output (JSON Response)

A JSON object containing the **timeframe granularity** and **time-series data** where timestamps are keys and the alert count is the value.

| JSON Key | Data Type | Description |
| :--- | :--- | :--- |
| `"Timeframe"` | `str` | The granularity of the aggregation: `"hour"`, `"day"`, or `"month"`. |
| Time Key (e.g., `"2023-06-15T14:00:00Z"`) | `int` | The number of alerts triggered within that time interval. |

### Example Output - Hour

Request: `start=2023-06-15T14:00:00Z` and `end=2023-06-15T16:00:00Z`
Alerts are aggregated by hour.

```json
{
  "Timeframe": "hour",
  "2023-06-15T14:00:00Z": 23,
  "2023-06-15T15:00:00Z": 43
}
```

### Example Output - Day

Request: `start=2023-06-15T00:00:00Z` and `end=2023-06-16T23:59:59Z`
Alerts are aggregated by day.

```json
{
  "Timeframe": "day",
  "2023-06-15T": 434,
  "2023-06-16T": 23
}
```

### Example Output - Month

Request: `start=2023-05-01T00:00:00Z` and `end=2023-06-31T23:59:59Z`
Alerts are aggregated by month.

```json
{
  "Timeframe": "month",
  "2023-06": 4344,
  "2023-05": 2332
}
```

-----

## World Map Chart API

This API provides the necessary data to render a world map view of alerts, showing the count of alerts at specific geographic points (latitude/longitude) within a country.

### Input Parameters (Query String)

| Parameter Name | Type | Description |
| :--- | :--- | :--- |
| `start` | `datetime` | Start datetime for filtering (captured in URL: `world_map_chart_api/start=...`). |
| `end` | `datetime` | End datetime for filtering (captured in URL: `world_map_chart_api/end=...`). |

### Expected Output (JSON Response)

A JSON list of dictionaries, where each dictionary represents an aggregation point (country/coordinates) and the total number of alerts triggered from that location. Geographic data is sourced from `config/buffalogs/countries_list.json`.

| JSON Key | Data Type | Description |
| :--- | :--- | :--- |
| `country` | `str` | The two-letter country code. |
| `lat` | `float` | The latitude of the aggregation point. |
| `lon` | `float` | The longitude of the aggregation point. |
| `alerts` | `int` | The total number of alerts triggered from these coordinates. |

### Example Output

```json
[
  {
    "country": "in",
    "lat": 27.0519,
    "lon": 75.7899,
    "alerts": 100
  },
  {
    "country": "jp",
    "lat": 35.8194,
    "lon": 139.9622,
    "alerts": 116
  },
  {
    "country": "us",
    "lat": 37.7468,
    "lon": -84.3014,
    "alerts": 90
  }
]
```

-----

## Risk Score API

This API returns the risk score for users whose score has been updated or changed within the specified timeframe.

### Input Parameters (Query String)

| Parameter Name | Type | Description |
| :--- | :--- | :--- |
| `start` | `datetime` | Start datetime for filtering (captured in URL: `risk_score_api/start=...`). |
| `end` | `datetime` | End datetime for filtering (captured in URL: `risk_score_api/end=...`). |

### Expected Output (JSON Response)

A JSON object where **usernames** are keys and their **current risk score** is the corresponding value.

| JSON Key | Data Type | Description |
| :--- | :--- | :--- |
| Username (e.g., `"Lorena Goldoni"`) | `str` | The current risk level for the user (e.g., `"No risk"`, `"High"`). |

### Example Output

```json
{
  "Lorena Goldoni": "No risk",
  "Lory Goldoni": "High"
}
```

-----

## Alerts API (`def list_alerts`)

The API handles an **HTTP GET** request to retrieve a filtered list of alert events.

-----

## Input Parameters (Query String)

The input is provided via **URL Query Parameters** (e.g., `?limit=10&start=...`). These parameters are validated and cleaned by `validate_alert_query` before being used for filtering.

| Parameter Name (Query Key) | Type | Description |
| :--- | :--- | :--- |
| **Pagination** | | |
| `limit` | `int` | Maximum number of results to return. |
| `offset` | `int` | Number of records to skip (for pagination). |
| **Date/Time Filters** | | |
| `start` | `str` | Start datetime for **alert creation** time. |
| `end` | `str` | End datetime for **alert creation** time. |
| `login_start_date` | `str` | Start datetime for the associated **login event**. |
| `login_end_date` | `str` | End datetime for the associated **login event**. |
| **Risk & Status Filters** | | |
| `risk_score` | `str/int` | Filter for a specific risk score value. |
| `min_risk_score` | `str/int` | Filter for alerts with a risk score greater than or equal to this value. |
| `max_risk_score` | `str/int` | Filter for alerts with a risk score less than or equal to this value. |
| `notified` | `str` | Filter by notification status (e.g., "true", "false"). |
| **User & Device Filters** | | |
| `user` | `str` | Filter by the user's username. |
| `name` | `str` | Filter by the alert rule name. |
| `ip` | `str` | Filter by IP address. |
| `country_code` | `str` | Filter by country code. |
| `is_vip` | `str` | Filter by VIP status. |
| `user_agent` | `str` | Filter by the User Agent string. |

-----

## Expected Output (JSON Response)

The output is a **JSON list** of alert objects, derived from the `AlertSerializer`.

| JSON Key | Data Type | Source Field | Description |
| :--- | :--- | :--- | :--- |
| **`created`** | `str` | `item.created` | The alert's creation timestamp, formatted as `YY-MM-DD HH:MM:SS`. |
| **`timestamp`** | `str` | `item.login_raw_data["timestamp"]` | The timestamp of the original login event. |
| **`triggered_by`** | `str` | `item.user.username` | The username associated with the alert. |
| **`severity_type`** | `str/int` | `item.user.risk_score` | The risk score of the user who triggered the alert. |
| **`rule_name`** | `str` | `item.name` | The name of the specific rule that was triggered. |
| **`rule_desc`** | `str` | `item.description` | A description of the triggered rule. |
| **`filter_type`** | `str` | `item.filter_type` | The category or type of filter/rule. |
| **`country`** | `str` | `item.login_raw_data["country"]` | The country code of the login event (converted to lowercase). |
| **`notified`** | `bool` | `bool(item.notified_status)` | A boolean indicating whether the alert has been notified/handled. |
| **`is_vip`** | `bool` | `item.is_vip` | A flag indicating if the associated user is a VIP. |

### Example Output

```json
[
  {
    "created": "24-10-02 12:00:00",
    "timestamp": "2024-10-02T12:00:00Z",
    "triggered_by": "alice_user",
    "severity_type": 5,
    "rule_name": "Impossible travel detected",
    "rule_desc": "Login from new country detected within 1 hour.",
    "filter_type": "Velocity Check",
    "country": "cn",
    "notified": false,
    "is_vip": true
  },
  {
    "created": "24-10-02 12:30:00",
    "timestamp": "2024-10-02T12:30:00Z",
    "triggered_by": "bob_user",
    "severity_type": 3,
    "rule_name": "Login from new country",
    "rule_desc": "First login from a new country for this user.",
    "filter_type": "Location Check",
    "country": "us",
    "notified": true,
    "is_vip": false
  }
]
```
