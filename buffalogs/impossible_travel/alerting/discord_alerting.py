import json

import requests
from impossible_travel.alerting.base_alerting import BaseAlerting
from impossible_travel.models import Alert


class DiscordAlerting(BaseAlerting):
    """
    Concrete implementation of the BaseQuery class for DiscordAlerting.
    """

    def __init__(self, alert_config: dict):
        """
        Constructor for the Discord Alerter query object.
        """
        super().__init__()
        self.webhook_url = alert_config.get("webhook_url")
        self.username = alert_config.get("username")

        if not self.webhook_url or not self.username:
            self.logger.error("Discord Alerter configuration is missing required fields.")
            raise ValueError("Discord Alerter configuration is missing required fields.")

    def notify_alerts(self):
        """
        Execute the alerter operation.
        """
        alerts = Alert.objects.filter(notified=False)
        for alert in alerts:
            alert_title, alert_description = self.alert_message_formatter(alert)

            discord_message = {
                "username": self.username,
                "embeds": [{"title": alert_title, "description": alert_description, "color": 16711680}],  # red
            }
            headers = {"Content-Type": "application/json"}
            try:
                resp = requests.post(self.webhook_url, headers=headers, data=json.dumps(discord_message))
                resp.raise_for_status()
                self.logger.info(f"Discord alert sent: {alert.name}")
                alert.notified = True
                alert.save()
            except requests.RequestException as e:
                self.logger.exception(f"Discord alert failed for {alert.name}: {str(e)}")
