## 2.6.x
### 2.6.0
#### Features
* Added healthcheck to the Postgres Docker container
#### Changes
* Moved documentation from Wiki to the project docs folder

## 2.5.x
### 2.5.0
#### Features
* Added some tests to the alerters (Google Summer of Code 2025 - @kunalsz)
* Added the `alert_types` API endpoint to list the supported alert types (Google Summer of Code 2025 - @noble47)
* Added Mattermost as new alerter type (Google Summer of Code 2025 - @kunalsz)
* Added RocketChat as new alerter type (Google Summer of Code 2025 - @kunalsz)
* Added GoogleChat as new alerter type (Google Summer of Code 2025 - @kunalsz)
#### Changes
* Created the `views` module in order to split the APIs
#### Bugfix
* Installed the curl command into the frontend Docker container to fix the healthcheck error

## 2.4.x
### 2.4.0
#### Features
* Added tests for the Opensearch ingestion source (by community - @sofie204)
* Added a new "alerts" page in the frontend with charts and filters (by community - @drona-gyawali)

### 2.3.x
### 2.3.0
#### Features
* Added some useful charts in the homepage to help detect user login behavior (by community - @drona-gyawali)
* Dockerized the Node Js frontend (by community - @drona-gyawali)
* Added the possibility to export the alerts in a CSV format from the homepage (by community - @eshant742)
#### Bugfix
* Fixed the detection using custom start_date and end_date in the impossible_travel management command (by community - @rskbansal)
* Fixed the homepage ValueError given by the lack of a return statement in the view (by community - @drona-gyawali)

### 2.2.x
### 2.2.0
#### Features
* Added the `Config.risk_score_increment_alerts` field in order to permit the selection of the alerts type which increment the User risk_score value (Default: ["New Country", "Anonymous IP Login", "Atypical Country", "Imp Travel"])
#### Changes
* Refactored the duplication of similar logic for processing date ranges, constructing API URLs, and error handling in the `requestdata.ts` file (by community - @eshant742)
* Refactored some functions in the `views.py` in order to provide more consistent timezone handling and to not rely on a fixed datetime string format (by community - @kunalsz)
* Refactored the user login dashboard in order to be compliant to the UI (by community - @noble47)
#### Bugfix
* Fixed the mismatch leading to TypeScript type‐checking errors and in order to follow the TS best practices (by community - @eshant742)

### 2.1.x
### 2.1.2
### Bugfix
* Handled splunklib import because it's a library not mandatory (if the default ingestion source used is Elasticsearch)
### 2.1.1
### Bugfix
* Fixed user-agent parsing in case of a "None" os
* Restored the NotifyAlertsTask task removed by mistake
### 2.1.0
#### Features
* Added the `Ingestion` process
* Added the Discord alerter (by community - @kunalsz)
* Added the Microsoft Teams alerter (by community - @drona-gyawali)
* Added the Opensearch ingestion source (by community - @rskbansal)
* Added the Splunk ingestion source (by community - @drona-gyawali)
### Changes
* Refactored the actual flow and the `BuffalogsProcessLogsTask` main task, in order to allow the implementation of more ingestion sources
* Refactored Hardcoded paths (by community - @kunalsz)
* Changed `links` to `networks` for elastic and kibana containers connection for deprecation [article [here](https://docs.docker.com/engine/network/links)] (by community - @rskbansal)
* Changed UI palette color (by community - @ragupari)
* Refactored the views to handle the new ingestion_factory paradigm (by community - @noble47)
### Bugfix
* Fixed the homepage resposive behaviour (by community - @ragupari)
* Fixed the "TypeError unique_logins() got an unexpected keyword argument 'pk_user'" in the frontend (by community - @drona-gyawali)
* Fixed the `csrf_token` reference in the frontend homepage, required by forms to protect against Cross-Site Request Forgery (CSRF) attacks (by community - @drona-gyawali)

### 2.0.x
### 2.0.0
#### Features
* Added the `Atypical Country` alert type, with the addition of the customizable field: **Config.atypical_country_days** in order to set from how many days a login from a Country is considered "Atypical"
* Added the `User Risk Threshold` alert type, with the customizable field: **Config.threshold_user_risk_alert** in order to set which level the user must have to trigger the "USER_RISK_THRESHOLD" alert
* Added the `Anonymous IP Login` alert type, in order to signal the logins made from an anonymizer IP
* Added the `Alerter` abstract class, in order to implement alerting sources for the alerts triggered
* Added the `Telegram` alerter (by community - @drona-gyawali)
* Added the `HTTP request` and `Webhook` alerters (by community - @Noble-47)
* Added the `Slack` alerter (by community - @Muhammad-Rebaal)
* Added the `Email` alerter (by community - @kunalsz)
* Added the `Pushover` alerter (by community - @kunalsz)
### Changes
* Changed the `Alert.is_filtered` field into a property
* Removed the setup.py method for tests and added the `tests-fixture` instead
* Refactoring on modules, removed: **impossible_travel.py**, **login_from_new_country.py** and **login_from_new_device.py**, in order to use just 2 files related to the main processes: `detection.py` and `alert_filter.py`
* Updated Certego shared CI to 1.5.0
* Updated containers: Elasticsearch and Kibana from 3.17.13 to 3.17.27
* Changed the **UserRiskScoreType.is_equal_or_higher(...)** method with the **UserRiskScoreType.compare_risk(...)** function
* Changed users risk_level ranges: [1,3] alerts = "Low" level, [4,6] alerts = "Medium" level, >= 7 alerts = "High" level
* Added debug logs for the Filter logic
* Removed the `update_risk_level()` function from the `BuffalogsCleanModelsPeriodicallyTask` periodic task. Now, the new risk_score is calculated as soon as an alert is triggered
### Bugfix
* Fixed the user-agent parser in the filtering
* Fixed the alerts.json.gz fixture (by community - @Noble-47)
* Fixed the admin visualization for the `is_filtered` and the `filter_type` fields
* Fixed the impossible_travel mgmt command
* Fixed the alert filters applied to users, in the `_update_users_filters` method
* Fixed elasticsearch port in *load_templates.sh* script
* Updated linters to solve conflicts in versions
* Added explicit version number to AG-Grid script source to fix javascript (by community - @Noble-47)
* Fixed the GUI widget resizing (by community - @drona-gyawali)

## 1.4.x
### 1.4.0
#### Features
* Implemented filter logic based on the custom Config set

## 1.3.x
### 1.3.2
### Changes
* Removed "version" property from docker-compose files because it is obsolete now
#### Bugfix
* Fixed migration 0011
### 1.3.1
### Changes
* Forced the existence of only 1 Config object with id=1
* Added Config.ignored_ISPs field for filtering known ISPs IPs
* Added forms: UserAdminForm, AlertAdminForm and ConfigAdminForm
* Added ShortLabelChoiceField to customize ChoiceField in order to show the short_value as label on DjangoValue
* Added MultiChoiceArrayField to customize ArrayField in order to support multiple choices
* Created MultiChoiceArrayWidget widget for user-friendly interface for ArrayField with multiple choices on Django Admin
* Updated some Python dependencies
#### Bugfix
* Fixed alert.name representation enums
### 1.3.0
#### Feature
* Added configuration panel in order to set custom preferences
* Added more fields in the Alert.login_raw_data dict in order to have more info about previous location for imp_travel detection
### Changes
* Set default settings values in the *settings.certego.py* file
* Moved Enums into *costants.py* file

## 1.2.x
### 1.2.12
#### Bugfix
* Cleaned venv from useless packages
* Added pytz in requirements because it's needed by celery_beat
* Registered UserAdmin in authentication
### 1.2.11
#### Bugfix
* Fixed the update of the login.updated field
* Added logging for the clear_models_periodically function
### 1.2.10
#### Changes
* Added settings into the Config model (instead of into the settings.py file)
### 1.2.9
#### Bugfix
* Fixed the connection to the buffalogs_postgres container
### 1.2.8
#### Bugfix
* Cleared requirements
### 1.2.7
#### Bugfix
* Fixed alert description format
### 1.2.6
#### Bugfix
* Removed linters from the setup app requirements
### 1.2.5
#### Bugfix
* Fixed index name from `fw` to `fw-proxy`
### 1.2.4
#### Bugfix
* Fixed ValueError('make_aware expects a naive datetime') in calc_distance function setting the timezone to True in the `Login.timestamp` model field
### 1.2.3
#### Bugfix
* Fixed KeyError('ip') in process_user function 
### 1.2.2
#### Bugfix
* Updated setup_config management command in order to overwrite the configs
### 1.2.1
#### Bugfix
* Fixed Elasticsearch environment variable
* Renamed shared tasks
### 1.2.0
#### Features
* Implemented Certego shared CI 1.3.5
#### Changes
* Renamed the Django settings constants and the environment variables
* Set manually the Elasticsearch port in the CI changing from 59200 to 9200

## 1.1.x
### 1.1.1
#### Bugfix
* Fixed symbolic link of the reusable app

### 1.1.0
#### Features
* Added `ignored_users` and `ignored_ips` in the Config model in order to filter some useless logins
* Added more details in the alerts
* Built the django reusable app for the impossible_travel app
* Creted the alerts fixture
* Added new GUI
* Developed some REST APIs

