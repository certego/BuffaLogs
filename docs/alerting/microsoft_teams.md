# Configuring Microsoft Teams Alerter for BuffaLogs

<p><i>This document outlines the steps to configure <b>Microsoft Teams</b> alerter for BuffaLogs to receive alerts via Microsoft Teams Webhooks.</i><p>

---

## Prerequisites

Before setting up the Microsoft Teams alerter, ensure the following:
- You have a Microsoft Business Account.
- You have admin permissions to configure Teams channels.
- BuffaLogs is installed and configured on your system.

---

## Steps to Implement

#### 1. Create an Incoming Webhook in Microsoft Teams
1. Open the Teams channel where alerts should be sent.
2. Click the **... (More options)** button next to the channel name.
3. Select **Connectors**.
4. Search for **Incoming Webhook** and click **Add**.
5. Configure the webhook by providing a name and optional image.
6. Click **Create** and copy the generated **Webhook URL** for later use.


#### 2. Update Configuration File
1. Open the BuffaLogs configuration file located at `config/buffalogs/alerting.json`.
2. Add or update the following JSON configuration with your Microsoft Teams webhook details:

    ```json
    {
        "active_alerters": ["microsoft_teams"],
        "microsoft_teams": {
            "webhook_url": "your-webhook-url"
        }
    }
    ```

3. Replace `"your-webhook-url"` with the webhook URL you copied earlier.
4. Save the file.

---

## Testing the Setup

1. Make sure the Docker containers are up and running.
2. Trigger the tests using the following command in your terminal:
    ```bash
    ./manage.py test impossible_travel.tests.alerters.test_alert_microsoft_teams.TestMicrosoftTeamsAlerting
    ```
**Extra Note**

3. To get a real test alert message in your MicrosoftTeams channel, add this code in `buffalogs/impossible_travel/tests/alerters/test_alert_microsoft_teams.py` :

    ```python
    def test_actual_alert(self):
        self.teams_alerting.notify_alerts()
    ```

4. Check the specified MicrosoftTeams channel to verify that the alert message has been received.
