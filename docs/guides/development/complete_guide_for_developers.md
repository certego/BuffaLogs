# Overview
BuffaLogs is a project for detecting anomalies in login data. In particular, after the collection of the login data which is stored on Elasticsearch and can be viewed on Kibana, BuffaLogs analyzes these logins and it uses internal logic to find unusual actions. 
Especially, the system can trigger 3 types of alerts: impossible travel, login from new device and login from new country.

Steps workflow for Developers:

1. All the developers have to set the enrivornment correctly &rarr; Follow [the System Configuration guide](#system-configuration)

   1a. Then, if you'd like to make front-end changes, so you need only to query the APIs &rarr; Upload [the fixture data](#fixture) and read the [API's section](https://github.com/certego/BuffaLogs/wiki/5.-REST-APIs) for more details about them

   1b. Otherwise, if you want to analyze the back-end development generating new data, please check [the BuffaLogs detection](#run-buffalogs-detection)

# System Configuration
Once you've cloned the project on your local device with `git clone git@github.com:certego/BuffaLogs.git`, follow the steps below in order to set up the environment correctly.
1. **Configure the Django-Admin.** 

   a. Apply the migrations into the database schema with `./manage.py migrate` 

   b. Create a superuser account (a user who has all permissions) with `./manage.py createsuperuser`

   c. Start the web server on the local machine launching `./manage.py runserver`
   ![image](https://github.com/certego/BuffaLogs/assets/33703137/3b86712f-a0c4-4f12-ad14-fb648361325a)

At this point, use the credentials set above to login at *localhost:8000/admin/*, where you will see the tables used by BuffaLogs for its detection logic and now they are empty because we haven't run the BuffaLogs detection, yet.
![image](https://github.com/certego/BuffaLogs/assets/33703137/b49e3f8c-84f8-4a40-bff7-7a8069866d36)

# Run BuffaLogs detections (Backend)
If this is the first time you're running BuffaLogs, you need to configure Elasticsearch first:

1. **Generate login data**

Run the `python random_example.py` script in the *examples* folder in order to create random login data in Elasticsearch. This simulates some audit logs that forward event to our Elasticsearch.

2. **Configure Elasticsearch.** 

   a. **Create index patterns.** Browse Kibana at *localhost:5601/* and create the index patterns selecting *Stack Management &rarr; Index Patterns*. 
   The indexes necessary to visualize correctly all the random login created are:

   | **Name** | **Timestamp field** | **Source** 
   | --- | --- | --- |
   | cloud-* | @timestamp | This index patter should match the source *cloud-test_data-<today>* |
   | fw-proxy-* | @timestamp | This index patter should match the source *fw-proxy-test_data-<today>* |
   | weblog-* | @timestamp | This index patter should match the source *weblog-test_data-<today>* |

   ![image](https://github.com/certego/BuffaLogs/assets/33703137/9e321693-3b61-4cc6-94ca-6c71aabd027b)

   b. **Load template.** Run the `./load_templates.sh` script in the */config/elasticsearch/* directory to upload the index template.
   Now, you should see the *example* template on Kibana in the *Stack Management &rarr; Index Management &rarr; Index Templates*
   ![image](https://github.com/certego/BuffaLogs/assets/33703137/2aae9551-2c8f-4bce-9bdd-d08919acac5b)

   c. You could visualize all the login data on Kibana in the *Discover* section, separated by the different index.
   ![image](https://github.com/certego/BuffaLogs/assets/33703137/34256765-0582-4a37-89b3-1df76d9ad79c)

Then, it is possible to run the detection manually via management command or automatically thanks to Celery.
  
### Run detection manually
You can start the detection thanks to the *impossible_travel* management command. 

In particular, if you simply launch `./manage.py impossible_travel`, it will start the detection analyzing the Elasticsearch login data saved in the previous half an hour. Indeed, the command will create an entry in the *TaskSettings* database to save the start and end datetime on which the detection has run.
![image](https://github.com/certego/BuffaLogs/assets/33703137/7dc86cc8-b686-4642-877d-88093122fbbf)

If you'd like to start the detection in a specific time frame, launch the command passing it the start and end arguments, for example: `./manage.py impossible_travel '2023-08-01 14:00:00' '2023-08-01 14:30:00'`. After that, you'll visualize the alerts returned by the BuffaLogs detection. 
      
It's possible to execute the detection directly into the Buffalogs container running the same command above, after entering into the bash with `docker compose -f docker-compose.yaml -f docker-compose.override.yaml -f docker-compose.elastic.yaml exec buffalogs bash`.

**NOTE - Attention to timestamp (again):** The alerts created timestamp will be relative to the moment in which you start the detection. This is important if you want to use the DRF APIs because some of them are referred to the timestamp of the login attempt and others to the alerts trigger timestamp. 

### Run detection Automatically

The BuffaLogs detection is a periodic Celery task. 

If you want to run it automatically, every 30 minutes, you have to start all the containers: `docker compose -f docker-compose.yaml -f docker-compose.override.yaml -f docker-compose.elastic.yaml up -d`. 

This command will run also Celery, Celery beat and Rabbitmq in order to handle the analysis in an automated way.

This is the way BuffaLogs is used in production; you can run `random_example.py` script to save new login data on Elasticsearch that will be processed automatically every 30 minutes when the task is ran.

# Test BuffaLogs Interface (Frontend)
It's possible to run the `./manage.py loaddata alerts` command in order to upload directly  BuffaLogs data on the database. The data loaded this way can be viewed in the Django-admin at `localhost:8000/admin` or from the GUI at `localhost:8000/`.

**Attention to timestamp for APIs responses:** The alerts triggered in this fixture are related to logins attempted at around  `Aug. 1, 2023, 2:00 p.m UTC` and `Aug. 1, 2023, 2:05 p.m UTC`, BUT the alerts have been triggered by BuffaLogs detection between `Aug. 1, 2023, 2:50 p.m. UTC` and `Aug. 1, 2023, 3:00 p.m. UTC`.

So, what about the APIs? If you load this fixture and want to get all the data with the DRF APIs, use them in these ways:
1. users_pie_chart_api is based on the `User.updated` field - http://localhost:8000/users_pie_chart_api/?start=2023-08-01T14:50:00Z&end=2023-08-01T14:55:00Z
2. alerts_line_chart_api is based on the `Alert.login_raw_data["timestamp"]` timeframe - for example:
   - HOUR implementation: http://localhost:8000/alerts_line_chart_api/?start=2023-08-01T13:00:00Z&end=2023-08-01T16:00:00Z
   - DAY partition: http://localhost:8000/alerts_line_chart_api/?start=2023-07-31T00:00:00Z&end=2023-08-01T23:59:59Z
   - MONTH division: http://localhost:8000/alerts_line_chart_api/?start=2023-07-01T00:00:00Z&end=2023-08-31T23:59:59Z
3. world_map_chart_api is based on the `Alert.login_raw_data["timestamp"]`, `Alert.login_raw_data["country"]`, `Alert.login_raw_data["lat"]` and `Alert.login_raw_data["lon"]` values - http://localhost:8000/world_map_chart_api/?start=2023-08-01T14:00:00Z&end=2023-08-01T14:05:00Z
4. alerts_api is based on the `Alert.created` field - http://localhost:8000/alerts_api/?start=2023-08-01T14:50:00Z&end=2023-08-01T14:55:00Z
5. risk_score_api is based on the `User.updated` value - http://localhost:8000/risk_score_api/?start=2023-08-01T14:50:00Z&end=2023-08-01T14:55:00Z

**NOTE: In order to visualize graphically the alerts triggered by BuffaLogs, browse to *localhost:8000/*. BuffaLogs doesn't send new data on Elasticsearch, there are stored only the logins attempt by the users, taken and analyze directly by BuffaLogs itself.**
