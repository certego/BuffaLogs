## BuffaLogs REST APIs

Five views were implemented using DRF - Django-Rest Framework, in order to provide the possible to query and produce the charts data.
In particular, the supplied APIs are:
| **API's name**| **API result**|
|---|---|
| *users_pie_chart_api* | It returns the association between the risk level and the number of users with that risk score |
| *alerts_line_chart_api* | It provides the number of alerts triggered in a particular timeframe |
| *world_map_chart_api* | It supplies the relation of countries and the number of alerts triggered from them |
| *alerts_api* | It offers the details about the alerts generated in the provided interval |
| *risk_score_api* | It provides the association between user and risk level for the users whose risk changed in the requested timeframe |

### Users pie chart API
| **API's name**| **API input**| **API output** |
|---|---|---|
| `users_pie_chart_api` | `start` and `end` datetime captured in the URL: `users_pie_chart_api/start=...&end=...` | a JSON with user risk as keys and user count as value |

Example:
```
{   "No risk": 32
    "Low": 2
    "Medium": 86
    "High": 4
}
```

### Alerts line chart API
| **API's name**| **API input**| **API output** |
|---|---|---|
| `alerts_line_chart_api` | `start` and `end` datetime captured in the URL: `alerts_line_chart_api/start=...&end=...` | A dictionary containing a list of datetime and a value representing the amount of data for that datetime |

The data is formatted differently based on start and end time duration. There are three types of formats:
* hour
* day
* month

#### Alerts line chart API - HOUR example
Request using start=2023-06-15T14:00:00Z and end=2023-06-15T16:00:00Z
```
{
 "Timeframe": "hour",
 "2023-06-15T14:00:00Z": 23,
 "2023-06-15T15:00:00Z": 43,
}
```
The first value represents the number of alerts triggered between 14:00:00Z and 15:00:00Z. the second represents the number of alerts triggered between 15:00:00Z and 16:00:00Z.

#### Alerts line chart API - DAY example
Request using start=2023-06-15T00:00:00Z and end=2023-06-16T23:59:59Z
```
{
 "Timeframe": "day"
 "2023-06-15T": 434,
 "2023-06-16T": 23
}
```

#### Alerts line chart API - MONTH example
Request using start=2023-05-01T00:00:00Z and end=2023-06-31:23:59:59Z
```
{
 "Timeframe": "month"
 "2023-06": 4344,
 "2023-05": 2332
}
```

### World map chart API
| **API's name**| **API input**| **API output** |
|---|---|---|
| `world_map_chart_api` | `start` and `end` datetime captured in the URL: `world_map_chart_api/start=...&end=...` | a list of dictionaries containing all the alerts triggered with the country (saved in the `impossible_travel/dashboard/countries.json` file), the latitude, the longitude and the number of alerts triggered from that place |

Example:
```
[
	{'country': 'in', 'lat': 27.0519, 'lon': 75.7899, 'alerts': 100},
 	{'country': 'in', 'lat': 26.9411, 'lon': 75.8773, 'alerts': 81},
		...
 	{'country': 'jp', 'lat': 35.8194, 'lon': 139.9622, 'alerts': 116},
 	{'country': 'jp', 'lat': 35.6728, 'lon': 139.715, 'alerts': 115},
		...
 	{'country': 'us', 'lat': 37.7468, 'lon': -84.3014, 'alerts': 90},
 	{'country': 'us', 'lat': 39.3745, 'lon': -76.6964, 'alerts': 84},
		...
]
```

### Alerts API
| **API's name**| **API input**| **API output** |
|---|---|---|
| `alerts_api` | `start` and `end` datetime captured in the URL: `alerts_api/start=...&end=...` | a JSON with a list of dictionaries each of which contains the timestamp, username and rule of the alert triggered |

Example:
```
[
	{
	 "timestamp": "2023-06-15T14:00:00Z",
	 "username": "Lorena Goldoni",
	 "rule_name": "Impossible travel detected"
	},
	{"timestamp": "2023-06-15T14:30:00Z",
	 "username": "Lorena Goldoni",
	 "rule_name": "Login from new country"
	}
]
```

### Risk Score API
| **API's name**| **API input**| **API output** |
|---|---|---|
| `risk_score_api` | `start` and `end` datetime captured in the URL: `risk_score_api/start=...&end=...` | a JSON with usernames as keys and the relative risk score as value |

Example:
```
{
	"Lorena Goldoni": "No risk",
	"Lory Goldoni": "High"
}
```