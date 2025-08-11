# Configuring Pushover Alerter for BuffaLogs

<p><i>This document outlines the steps to configure <b>Pushover</b> alerter for BuffaLogs to receive alerts via Pushover notifications.</i><p>

---

## Prerequisites

Before setting up the Pushover alerter, ensure the following:
- You have a Pushover account.
- You have created an application in Pushover to obtain an API token.
- BuffaLogs is installed and configured on your system.

---

## Steps to Implement

#### 1. Create a Pushover Application
1. Log in to your Pushover account.
2. Navigate to [Pushover Apps](https://pushover.net/apps).
3. Click **Create an Application/API Token**.
4. Fill in the required details and click **Create Application**.
5. Copy the generated **API Token** for later use.

#### 2. Get Your User Key
1. Log in to your Pushover account.
2. Navigate to your [Dashboard](https://pushover.net/dashboard).
3. Copy your **User Key** from the dashboard.

#### 3. Update Configuration File
1. Open the BuffaLogs configuration file located at `config/buffalogs/alerting.json`.
2. Add or update the following JSON configuration with your Pushover details:

    ```json
    {
        "active_alerters": ["pushover"],
        "pushover": {
            "api_token": "your-api-token",
            "user_key": "your-user-key"
        }
    }
    ```

3. Replace `"your-api-token"` and `"your-user-key"` with the values you obtained earlier.
4. Save the file.

---

## Testing the Setup

1. Make sure the Docker containers are up and running.
2. Trigger the tests using the following command in your terminal:
    ```bash
    ./manage.py test impossible_travel.tests.alerters.test_alert_pushover.TestPushoverAlerting
    ```
**Extra Note**

3. To get a real test alert message in your pushover channel, add this code in `buffalogs/impossible_travel/tests/alerters/test_alert_pushover.py` :

    ```python
    def test_actual_alert(self):
        self.pushover_alerting.notify_alerts()
    ```

4. Check the specified Pushover channel to verify that the alert message has been received.