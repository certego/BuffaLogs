# Configuring Mattermost Alerter for BuffaLogs

<p><i>This document outlines the steps to configure <b>Mattermost</b> alerter for BuffaLogs to receive alerts via Mattermost Webhooks.</i><p>

---

## Prerequisites

Before setting up the Mattermost alerter, ensure the following:
- You have a Mattermost account.
- You have admin permissions to create webhooks in Mattermost.
- BuffaLogs is installed and configured on your system.

---

## Steps to Implement

#### 1. Create an Incoming Webhook
1. Go to **Main Menu** → **Integrations** → **Incoming Webhooks**.
2. Click **Add Incoming Webhook**.
3. Select the channel where alerts will be published.
4. Give it a name like "BuffaLogs Alert Bot".
5. Click **Save** and copy the generated **Webhook URL** for later use.
6. To use the username you just set up for your alerts:
    - Go to **System Console** → **Integrations** → **Integration Management**.
    - Set **Enable integrations to override usernames** to `True`.


#### 2. Update Configuration File
1. Open the BuffaLogs configuration file located at `config/buffalogs/alerting.json`.
2. Add or update the following JSON configuration with your Mattermost webhook details:

    ```json
    {
        "active_alerters": ["mattermost"],
        "mattermost": {
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
    ./manage.py test impossible_travel.tests.alerters.test_alert_mattermost.TestMattermostAlerting
    ```
**Extra Note**

3. To get a real test alert message in your Mattermost channel, add this code in `buffalogs/impossible_travel/tests/alerters/test_alert_mattermost.py` :

    ```python
    def test_actual_alert(self):
        self.mattermost_alerting.notify_alerts()
    ```

4. Check the specified Mattermost channel to verify that the alert message has been received.