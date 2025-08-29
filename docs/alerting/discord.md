# Configuring Discord Alerter for BuffaLogs

<p><i>This document outlines the steps to configure <b>Discord</b> alerter for BuffaLogs to receive alerts via the Discord Webhooks.</i><p>

---

## Prerequisites

Before setting up the Discord alerter, ensure the following:
- You have a Discord account.
- You are an admin or have the necessary permissions to create webhooks in a Discord server.
- BuffaLogs is installed and configured on your system.

---

## Steps to Implement

#### 1. Create a Webhook URL
1. Log in to your Discord account.
2. Create a server on Discord if you don't already have one.
3. Ensure you have admin permissions for the server.
4. Navigate to **Server Settings** → **Integrations** → **Webhooks**.
5. Click **New Webhook** and select the channel where you want to receive alerts.
6. Copy the generated **Webhook URL** and save it for later use.


#### 2. Update Configuration File
1. Open the BuffaLogs configuration file located at `config/buffalogs/alerting.json`.
2. Add or update the following JSON configuration with your Discord webhook details:

    ```json
    {
        "active_alerters": ["discord"],
        "discord": {
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
    ./manage.py test impossible_travel.tests.alerters.test_alert_discord.TestDiscordAlerting
    ```
**Extra Note**

3. To get a real test alert message in your Discord channel, add this code in `buffalogs/impossible_travel/tests/alerters/test_alert_discord.py` :

    ```python
    def test_actual_alert(self):
        self.discord_alerting.notify_alerts()
    ```

4. Check the specified Discord channel to verify that the alert message has been received.
