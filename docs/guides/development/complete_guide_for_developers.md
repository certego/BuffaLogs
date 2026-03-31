# Overview
BuffaLogs is a project for detecting anomalies in login data. In particular, after the collection of the login data which is stored on Elasticsearch and can be viewed on Kibana, BuffaLogs analyzes these logins and it uses internal logic to find unusual actions. 
Especially, the system can trigger 3 types of alerts: impossible travel, login from new device and login from new country.

Steps workflow for Developers:

1. All the developers have to set the enrivornment correctly &rarr; Follow [the System Configuration guide](#system-configuration)

   **Alternative Setup**: For a containerized **backend** development environment with all dependencies pre-configured, see [Development with DevContainers](development_with_devcontainers.md).

   1a. Then, if you'd like to make front-end changes, so you need only to query the APIs &rarr; Upload [the fixture data](#fixture) and read the [API's section](docs/rest-apis.md) for more details about them

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

# Setting Up Alerters
Different types of alerters are available in BuffaLogs as per your requirement of getting alert notifications about login anamolies. Either you can use the already defined alerters or code a new easily in the same format of the other alerters.

### Configuring an already implemented Alerter
Setting up a precoded alerter is a simple task. All you need to do is add your configurations to the `alerting.json` file, include your alerter in the `active_alerters` list, and you're all set! For detailed, step-by-step instructions for each alerter, refer to `docs/alerting`.

### Implementing a new Alerter
This process requires you to implement a new alerter but, not entirely from scratch. You can use the structure of the existing alerters as a reference, with DiscordAlerting as an example.

1. **Import the necessary libraries**
```
import json
import requests
from collections import defaultdict
import backoff
from django.db.models import Q
from impossible_travel.alerting.base_alerting import BaseAlerting
from impossible_travel.models import Alert
```

2. **Setup the Alerting class**
This step involves setting up your configurations for the alerter.
```
class DiscordAlerting(BaseAlerting):
    """
    Concrete implementation of the BaseQuery class for DiscordAlerting.
    """

    def __init__(self, alert_config: dict):
        """
        Constructor for the Discord Alerter query object.
        """
        super().__init__()
        # Get your configurations from the alerting.json file here
        self.webhook_url = alert_config.get("webhook_url")
        self.username = alert_config.get("username")

        # Check if they are empty or not bymistake leading to errors
        if not self.webhook_url or not self.username:
            self.logger.error("Discord Alerter configuration is missing required fields.")
            raise ValueError("Discord Alerter configuration is missing required fields.")

```

3. **send_message**
This function is responsible for sending the actual requests.
`backoff` has been used to retry sending the alerts if they fail for any network reasons,you can configure that based on your needs.
It takes 3 parameters here(you can add more specific to your alerter):-
- The alert itself
- The alert title
- And the alert description
If the last two are not provided a default template is used to get the title and the description based on the `alert`.
```
   @backoff.on_exception(backoff.expo, requests.RequestException, max_tries=5, base=2)
   def send_message(self, alert, alert_title=None, alert_description=None):
      if alert_title is None and alert_description is None and alert:
         alert_title, alert_description = self.alert_message_formatter(alert)

      # Your alert message structure goes in here, it will vary depending upon your source. Look up for documentations of your source on how to send messages to the preffered channel.
      alert_msg = {
         "username": self.username,
         "embeds": [{"title": alert_title, "description": alert_description, "color": 16711680}],  # red
      }
      headers = {"Content-Type": "application/json"}

      resp = requests.post(self.webhook_url, headers=headers, data=json.dumps(alert_msg))
      resp.raise_for_status()
      return resp
```

4. **send_scheduled_summary**
This function is responsible for sending a summary of alerts over a specified time period(daily/weekly). It is not directly executed here instead the scheduled task `ScheduledAlertSummaryTask` executes it based on the input frequency. Here's how it works:-
- Format the summary
   - Uses the `alert_message_formatter` from `BaseAlerting` to generate summary title and description using the `alert_template_summary.jinja` jinja template.
   - The summary includes details such as the total number of alerts, user breakdown, and alert breakdown.
- Send the summary
   - Calls the `send_message` method to send the formatted summary as a notification.

There is nothing much to change here except the name of the alerter you will be using,you can simply copy paste this part!
```
   def send_scheduled_summary(self, start_date, end_date, total_alerts, user_breakdown, alert_breakdown):
      summary_title, summary_description = self.alert_message_formatter(
         alert=None,
         template_path="alert_template_summary.jinja",
         start_date=start_date,
         end_date=end_date,
         total_alerts=total_alerts,
         user_breakdown=user_breakdown,
         alert_breakdown=alert_breakdown,
      )

      try:
         self.send_message(alert=None, alert_title=summary_title, alert_description=summary_description)
         self.logger.info(f"Discord Summary Sent From: {start_date} To: {end_date}")
      except requests.RequestException as e:
         self.logger.exception(f"Discord Summary Notification Failed: {str(e)}")
```

5. **notify_alerts**
This function executes the alerter operation by processing and sending notifications for triggered alerts. It is designed to handle both individual and grouped alerts efficiently, ensuring that notifications are sent reliably while maintaining the status of each alert. Here's how it works:-
- First of all it filters the alerts for which the notified status is `False`, also if `start_date` and `end_date` are provided, alerts are filtered within that range. (Used in `ScheduledAlertSummaryTask` task)
- Next similar alerts are grouped by the combination of `username` and `alert name`.
- Sending notification:
   - For a single alert in the group(single alert in the 30 min window)
      - Sends a notification using the `send_message` method.
      - And updates the `notified_status` to mark the alert as sent.
   - For multiple alerts in a group(multiple alerts in the 30 min window)
      - Formats a clubbed notification using a template.
      - Sends the clubbed notification.
      - Updates the notified_status for all alerts in the group.

The code doesn't need any alteration,you can just copy paste it by changing `discord` here with your alerter name.
```
   def notify_alerts(self, start_date=None, end_date=None):
      """
      Execute the alerter operation.
      """
      alerts = Alert.objects.filter((Q(notified_status__discord=False) | ~Q(notified_status__has_key="discord")))
      if start_date is not None and end_date is not None:
         alerts = Alert.objects.filter(
               (Q(notified_status__discord=False) | ~Q(notified_status__has_key="discord")) & Q(created__range=(start_date, end_date))
         )

      grouped = defaultdict(list)
      for alert in alerts:
         key = (alert.user.username, alert.name)
         grouped[key].append(alert)

      for (username, alert_name), group_alerts in grouped.items():
         if len(group_alerts) == 1:
               try:
                  alert = group_alerts[0]
                  self.send_message(alert=alert)
                  self.logger.info(f"Discord alert sent: {alert.name}")
                  alert.notified_status["discord"] = True
                  alert.save()
               except requests.RequestException as e:
                  self.logger.exception(f"Discord Notification Failed for {alert}: {str(e)}")

         else:
               alert = group_alerts[0]
               alert_title, alert_description = self.alert_message_formatter(alert=alert, template_path="alert_template_clubbed.jinja", alerts=group_alerts)
               try:
                  self.send_message(alert=None, alert_title=alert_title, alert_description=alert_description)
                  self.logger.info(f"Clubbed Discord Alert Sent: {alert_title}")

                  for a in group_alerts:
                     a.notified_status["discord"] = True
                     a.save()
               except requests.RequestException as e:
                  self.logger.exception(f"Clubbed Discord Alert Failed for {group_alerts}: {str(e)}")
```

6. **Finally ,configure the `alerting.json` file by setting up your configurations as shown below.**
```,
{
    "active_alerters": ["discord"],
    "discord" : {
        "webhook_url" : "https://discord.com/api/webhooks/WEBHOOK",
        "username" : "BuffaLogs_Alert"
    },
}
```

### Writing tests for your Alerter
Comprehensive testing is absolutely necessary anywhere. Here's how you can write tests for your alerter,using `TestDiscordAlerting` here as an example:-

1. **Import the required libraries**
```
import json
from datetime import timedelta
from unittest.mock import MagicMock, patch

import requests
from django.test import TestCase
from django.utils import timezone
from impossible_travel.alerting.base_alerting import BaseAlerting
from impossible_travel.alerting.discord_alerting import DiscordAlerting
from impossible_travel.models import Alert, Login, User
```

2. **Setup the `TestDiscordAlerting` class**
Setup your configs here from the `alerting.json` file.
Create users and alerts based upon your needs.
```
class TestDiscordAlerting(TestCase):
   @classmethod
   def setUpTestData(cls):
      """Set up test data once for all tests."""
      cls.discord_config = BaseAlerting.read_config("discord")
      cls.discord_alerting = DiscordAlerting(cls.discord_config)

      cls.user = User.objects.create(username="testuser")
      Login.objects.create(user=cls.user, id=cls.user.id)

      cls.alert = Alert.objects.create(
         name="Imp Travel",
         user=cls.user,
         notified_status={"discord": False},
         description="Impossible travel detected",
         login_raw_data={},
      )
```

3. **test_send_alert**
The simplest and most important of all tests, mock the sending of alert message and verify if the content is as expected.
Use `your_alerter_alerting` instead of `discord_alerting`.
```
   @patch("requests.post")
   def test_send_alert(self, mock_post):
      """Test that a properly formed alert is sent via POST"""
      mock_post.return_value = MagicMock(status_code=200)

      self.discord_alerting.notify_alerts()

      expected_title, expected_description = BaseAlerting.alert_message_formatter(self.alert)
      expected_payload = {
         "username": self.discord_config["username"],
         "embeds": [
               {
                  "title": expected_title,
                  "description": expected_description,
                  "color": 16711680,
               }
         ],
      }

      mock_post.assert_called_once_with(
         self.discord_config["webhook_url"],
         headers={"Content-Type": "application/json"},
         data=json.dumps(expected_payload),
      )
```

4. **test_no_alerts**
Testing if no alerts are being notified if none is present.
```
   @patch("requests.post")
   def test_no_alerts(self, mock_post):
      """Test that no alerts are sent when there are no alerts to notify"""
      for alert in Alert.objects.all():
         alert.notified_status["discord"] = True
         alert.save()
      self.discord_alerting.notify_alerts()
      self.assertEqual(mock_post.call_count, 0)
```

5. **test_improper_config**
Testing if improper/empty config would raise ValueError.
```
   def test_improper_config(self):
      """Test that an error is raised if the configuration is not correct"""
      with self.assertRaises(ValueError):
         DiscordAlerting({})
```

6. **test_alert_network_failure**
Testing no alert is being sent or marked notified is there's a network failure.
```
   @patch("requests.post")
   def test_alert_network_failure(self, mock_post):
      """Test that alert is not marked as notified if there are any Network Fails"""
      # Simulate network/API failure
      mock_post.side_effect = requests.RequestException()

      self.discord_alerting.notify_alerts()

      # Reload the alert from DB to check its state
      alert = Alert.objects.get(pk=self.alert.pk)
      self.assertFalse(alert.notified_status["discord"])
```

7. **test_clubbed_alerts**
Testing if multiple similar alerts are being clubbed together into a single notification
```
   @patch("requests.post")
      def test_clubbed_alerts(self, mock_post):
         """Test that multiple similar alerts are clubbed into a single notification."""
         now = timezone.now()
         start_date = now - timedelta(minutes=30)
         end_date = now

         # Create two alerts within the 30min window
         alert1 = Alert.objects.create(
            name="Imp Travel",
            user=self.user,
            notified_status={"discord": False},
            login_raw_data={},
         )
         alert2 = Alert.objects.create(
            name="Imp Travel",
            user=self.user,
            notified_status={"discord": False},
            login_raw_data={},
         )
         alert3 = Alert.objects.create(
            name="New Country",
            user=self.user,
            notified_status={"discord": False},
            login_raw_data={},
         )

         Alert.objects.filter(id=alert1.id).update(created=start_date + timedelta(minutes=10))
         Alert.objects.filter(id=alert2.id).update(created=start_date + timedelta(minutes=20))
         # This alert won't be notified as it's outside of the set range
         Alert.objects.filter(id=alert3.id).update(created=start_date - timedelta(hours=2))
         alert1.refresh_from_db()
         alert2.refresh_from_db()
         alert3.refresh_from_db()

         mock_response = MagicMock()
         mock_response.status_code = 200
         mock_post.return_value = mock_response

         self.discord_alerting.notify_alerts(start_date=start_date, end_date=end_date)

         args, kwargs = mock_post.call_args
         # Based upon your alerter extract the required content to verify
         data = kwargs["data"]

         # 3 Imp Travel Alerts will be clubbed
         self.assertIn("BuffaLogs - Login Anomaly Alerts : 3", data)
         # Reload the alerts from the db
         alert1 = Alert.objects.get(pk=alert1.pk)
         alert2 = Alert.objects.get(pk=alert2.pk)
         alert2 = Alert.objects.get(pk=alert3.pk)

         self.assertTrue(alert1.notified_status["discord"])
         self.assertFalse(alert2.notified_status["discord"])
         # The last alert is not notified as expected
         self.assertFalse(alert3.notified_status["discord"])
```

Similarly you can add more tests depending upon your usage case.
