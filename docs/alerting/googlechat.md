# Configuring Google Chat Alerter for BuffaLogs

<p><i>This document outlines the steps to configure <b>Google Chat</b> alerter for BuffaLogs to receive alerts via Google Chat Webhooks.</i><p>

---

## Prerequisites

Before setting up the Google Chat alerter, ensure the following:
- You have a Google account.
- You have access to a Google Chat Space.
- BuffaLogs is installed and configured on your system.

---

## Steps to Implement

#### 1. Create a Google Chat Space
1. Go to [Google Chat](https://chat.google.com).
2. Create or open an existing Space (a group chat or channel).

#### 2. Add a Webhook to the Space
1. In the Space, navigate to **Apps & Integrations** → **Webhooks**.
2. Click **Add Webhook**.
3. Give it a name like "BuffaLogs Alert Bot".
4. Click **Save** and copy the generated **Webhook URL** for later use.

#### 3. Update Configuration File
1. Open the BuffaLogs configuration file located at `config/buffalogs/alerting.json`.
2. Add or update the following JSON configuration with your Google Chat webhook details:

    ```json
    {
        "active_alerters": ["googlechat"],
        "googlechat": {
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
    ./manage.py test impossible_travel.tests.alerters.test_alert_googlechat.TestGoogleChatAlerting
    ```
**Extra Note**

3. To get a real test alert message in your googlechat channel, add this code in `buffalogs/impossible_travel/tests/alerters/test_alert_googlechat.py` :

    ```python
    def test_actual_alert(self):
        self.googlechat_alerting.notify_alerts()
    ```

4. Check the specified GoogleChat channel to verify that the alert message has been received.