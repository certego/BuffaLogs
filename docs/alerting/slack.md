# Configuring Slack Alerter for BuffaLogs

<p><i>This document outlines the steps to configure <b>Slack</b> alerter for BuffaLogs to receive alerts via Slack Webhooks.</i><p>

---

## Prerequisites

Before setting up the Slack alerter, ensure the following:
- You have a Slack account.
- You have admin permissions to create webhooks in Slack.
- BuffaLogs is installed and configured on your system.

---

## Steps to Implement

#### 1. Create a Slack App
1. Go to [Slack API](https://api.slack.com/apps).
2. Click **Create New App**.
3. Choose **From scratch**.
4. Name your app (e.g., "BuffaLogs Alerts") and select your workspace.

#### 2. Configure Incoming Webhooks
1. In your app's settings, go to **Incoming Webhooks**.
2. Toggle **Activate Incoming Webhooks** to `On`.
3. Click **Add New Webhook to Workspace**.
4. Select the channel where you want to receive alerts.
5. Copy the generated **Webhook URL** for later use.


#### 3. Update Configuration File
1. Open the BuffaLogs configuration file located at `config/buffalogs/alerting.json`.
2. Add or update the following JSON configuration with your Slack webhook details:

    ```json
    {
        "active_alerters": ["slack"],
        "slack": {
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
    ./manage.py test impossible_travel.tests.alerters.test_alert_slack.TestSlackAlerting
    ```
**Extra Note**

3. To get a real test alert message in your Slack channel, add this code in `buffalogs/impossible_travel/tests/alerters/test_alert_slack.py` :

    ```python
    def test_actual_alert(self):
        self.slack_alerting.notify_alerts()
    ```

4. Check the specified Slack channel to verify that the alert message has been received.