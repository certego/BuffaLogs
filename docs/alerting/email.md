# Configuring Email Alerter for BuffaLogs

<p><i>This document outlines the steps to configure <b>Email</b> alerter for BuffaLogs to receive alerts via email notifications.</i><p>

---

## Prerequisites

Before setting up the Email alerter, ensure the following:
- You have access to an SMTP server (e.g., Gmail, Outlook, etc.).
- You have the SMTP server details (host, port, username, and password).
- BuffaLogs is installed and configured on your system.

---

## Steps to Implement

#### 1. Obtain SMTP Server Details
1. Identify the SMTP server you will use (e.g., Gmail, Outlook, etc.).
2. Note down the following details:
    - SMTP Host (e.g., `smtp.gmail.com` for Gmail).
    - SMTP Port (e.g., `587` for Gmail).
    - Your email address (used as the username).
    - Your email password or app-specific password (if required).


#### 2. Update Configuration File
1. Open the BuffaLogs configuration file located at `config/buffalogs/alerting.json`.
2. Add or update the following JSON configuration with your SMTP details:

    ```json
    {
        "active_alerters": ["email"],
        "email": {
            "email_server": "your-email-host",
            "email_port": 587,
            "email_use_tls" : "True",
            "email_host_user" : "SENDER_EMAIL",
            "email_host_password" : "SENDER_APP_PASSWORD",
            "default_from_email" : "BuffaLogs Alerts SENDER_EMAIL",
            "recipient_list_admins" : ["RECEIVER_EMAIL_ADDRESS", "RECEIVER_EMAIL_ADDRESS_2"],
            "recipient_list_users": {"testuser": "testuser@test.com"}
        }
    }
    ```

3. Replace the placeholders with your SMTP server details.
4. Save the file.

---

## Testing the Setup

1. Make sure the Docker containers are up and running.
2. Trigger the tests using the following command in your terminal:
    ```bash
    ./manage.py test impossible_travel.tests.alerters.test_alert_email.TestEmailAlerting
    ```
**Extra Note**

3. To get a real test alert message in your receiver email address, add this code in `buffalogs/impossible_travel/tests/alerters/test_alert_email.py` :

    ```python
    def test_actual_alert(self):
        self.email_alerting.notify_alerts()
    ```

4. Check the specified receiver email address to verify that the alert message has been received.
