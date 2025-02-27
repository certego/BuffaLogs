import json

import requests
from impossible_travel.alerting.base_alerting import BaseAlerting
from impossible_travel.models import Alert


class SlackAlerting(BaseAlerting):
    def __init__(self, alert_config: dict):
        """
        Constructor for the Slack Alerter object.
        """
        super().__init__()
        self.webhook_url = alert_config.get("webhook_url")
        if not self.webhook_url:
            self.logger.error("Missing required 'webhook_url' in alert_config")

    def notify_alerts(self):
        """
        Execute the alerter operation - send all unnotified alerts to Slack.
        """
        alerts = Alert.objects.filter(notified=False)

        for alert in alerts:
            # alert message
            alert_msg = (
                f"Login Anomaly Alert: {alert.name}\nDear user,\n\nAn unusual login activity has been detected:\n\n{alert.description}\n\nStay Safe,\nBuffalogs"
            )

            payload = {"text": alert_msg}
            response = requests.post(self.webhook_url, data=json.dumps(payload), headers={"Content-Type": "application/json"})
            if response.status_code != 200:
                self.logger.error("Failed to send alert to Slack (status %s): %s", response.status_code, response.text)

            self.logger.info("Alerting Slack about: %s", alert.name)
            alert.notified = True
            alert.save()
