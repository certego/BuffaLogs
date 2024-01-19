## 1.3.x
## 1.3.0
#### Changes
* Changed the *new_country* alert logic: previously, if the new country has already been reported, the alert wasn't triggered again; now, after *CERTEGO_BUFFALOGS_NEW_COUNTRY_ALERT_FILTER* days from the first alert, it can be triggered again

## 1.2.x
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

