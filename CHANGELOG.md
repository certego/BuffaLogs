## 2.x.x
### 2.0.0
#### Features
* Added `Atypical Country` alert, with the addition of the customizable field: **Config.atypical_country_days** in order to set from how many days a login from a Country is considered "Atypical"
* Added `User Risk Threshold` alert, with the customizable field: **Config.threshold_user_risk_alert** in order to set which level the user must have to trigger the "USER_RISK_THRESHOLD" alert
### Changes
* Refactoring on modules, removed: **impossible_travel.py**, **login_from_new_country.py** and **login_from_new_device.py**, in order to use just 3 modules for the 3 main processes: `ingestion_handler.py`, `detection.py` and `alert_filter.py`
* Updated Certego shared CI to 1.5.0
* Updated containers: Elasticsearch and Kibana from 3.17.13 to 3.17.27
* Changed the **UserRiskScoreType.is_equal_or_higher(...)** method with the **UserRiskScoreType.compare_risk(...)** function
* Changed users risk_level ranges: [1,3] alerts = "Low" level, [4,6] alerts = "Medium" level, >= 7 alerts = "High" level
* Added debug logs for the Filter logic
* Removed the `update_risk_level()` function from the `BuffalogsCleanModelsPeriodicallyTask` periodic task. Now, the new risk_score is calculated as soon as an alert is triggered
### Bugfix
* Fixed elasticsearch port in *load_templates.sh* script
* Updated linters to solve conflicts


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

