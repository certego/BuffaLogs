# Configuring RocketChat Alerter for BuffaLogs

<p><i>This document outlines the steps to configure <b>RocketChat</b> alerter for BuffaLogs to receive alerts via RocketChat Webhooks.</i><p>

---

## Prerequisites

Before setting up the RocketChat alerter, ensure the following:
- You have a RocketChat account.
- You have admin permissions to create webhooks in RocketChat.
- BuffaLogs is installed and configured on your system.

---

## Steps to Implement

#### 1. Create an Incoming Webhook
1. Go to **Administration** → **Integrations** → **New Integration**.
2. Choose **Incoming Webhook**.
3. Configure the webhook:
    - Set the username from which alerts will be posted.
    - Set the channel where alerts will be posted.
    - Check **Enabled**.
4. Save and copy the generated **Webhook URL** for later use.


#### 2. Update Configuration File
1. Open the BuffaLogs configuration file located at `config/buffalogs/alerting.json`.
2. Add or update the following JSON configuration with your RocketChat webhook details:

    ```json
    {
        "active_alerters": ["rocketchat"],
        "rocketchat": {
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
    ./manage.py test impossible_travel.tests.alerters.test_alert_rocketchat.TestRocketChatAlerting
    ```
**Extra Note**

3. To get a real test alert message in your RocketChat channel, add this code in `buffalogs/impossible_travel/tests/alerters/test_alert_rocketchat.py` :

    ```python
    def test_actual_alert(self):
        self.rocketchat_alerting.notify_alerts()
    ```

4. Check the specified RocketChat channel to verify that the alert message has been received.
