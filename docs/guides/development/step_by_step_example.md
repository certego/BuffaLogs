##  A Step by step Example
It is possible to create random logs to test the project just by running the commands below:
1. Launch Elasticsearch and Kibana with the `docker compose -f docker-compose.yaml -f docker-compose.elastic.yaml up -d elasticsearch kibana` command`
2. Load the Elastic Common Schema template running the `./load_templates.sh` script
3. Create the random test data launching the Python script from the *buffalogs_module/examples* folder: `python random_example.py`
4. Go on Kibana at `localhost:5601` &rarr; **Stack Management** &rarr; **Index Patterns** and create a new Index pattern with `cloud-*` as name and select `@timestamp` for the timestamp field
5. Check: Now, you should be able to visualize 2000 Docs count at **Stack management** &rarr; **Index Management** for the `cloud-<today_date>` index

And you can analyze the logs data newly uploaded at `localhost:5601`

![buffalogs_example_kibana_page](https://user-images.githubusercontent.com/33703137/220941321-1f0c637a-b5c5-4a2c-bbe5-3730c44d9d5e.png)

At this stage, it is your choice to run the application **manually** or **automatically** (using Celery).

First of all, you have to apply the migrations in order to propagate changes from your models into the database shema. To do that, launch `./manage.py makemigrations` for creating new migrations based on the changes made in the models, if some have been made. then, apply the migrations running `./manage.py migrate`.

#### Running Manually
To run the application manually, launch the management command below from *buffalogs_module/buffalogs*:
```bash
python manage.py impossible_travel
```
This command can also be launched with a specific time range which the detection will be taken:
```bash
python manage.py impossible_travel '2023-08-01 00:00:00' '2023-08-01 3:00:00'
```
You can also clear all the data saved in the database just running:
```bash
python manage.py clear_models
```

#### Running Automatically
To run it in an automated way, just start up all the tools with:
```bash
sudo docker compose up -d
```

### Results
In both cases, the results are available at `localhost:80`
#### Dashboard Page
![buffalogs_dashboard_screenshot](https://user-images.githubusercontent.com/33703137/220879987-b6453e9d-0129-45c1-bc26-0542005e8730.png)
#### Users Page
![buffalogs_users_page](https://user-images.githubusercontent.com/33703137/220947957-a03dc912-a264-4e7f-ba48-eec700649f43.png)
#### All Logins associated to the user
![buffalogs_all_logins_page](https://user-images.githubusercontent.com/33703137/220948055-046a4b64-5531-419d-b1d3-37dd49f29290.png)
#### Unique Logins 
Just the details of the logins with different user agents or countries
![buffalogs_unique_logins_page](https://user-images.githubusercontent.com/33703137/220948503-42dbe97e-773a-4b31-84b4-7835a5c24b72.png)
#### Alerts related to the user
![buffalogs_alerts_page](https://user-images.githubusercontent.com/33703137/220948677-bbaf2ef7-d740-4d93-a024-ed6d57579272.png)