import json

import requests
from impossible_travel.alerting.base_alerting import BaseAlerting
from impossible_travel.models import Alert


class DiscordAlerting(BaseAlerting):
    """
    Concrete implementation of the BaseQuery class for Discord.
    """

    def __init__(self, alert_config: dict):
        """
        Constructor for the Discord Alerter query object.
        """
        super().__init__()
        # here we can access the alert_config to get the configuration for the alerter
        self.webhook_url = alert_config.get("webhook_url")

    def notify_alerts(self):
        """
        Execute the alerter operation.
        """
        alerts = Alert.objects.filter(notified=False)
        for alert in alerts:
            # the alert message to send
            alert_msg = f"Dear user,\n\nAn unusual login activity has been detected:\n\n{alert.description}\n\nStay Safe,\nBuffalogs"

            discord_message = {
                "username": "BuffaLogs Alert",
                "embeds": [{"title": f"Login Anomaly Alert: {alert.name}", "description": alert_msg, "color": 16711680}],  # red
            }

            headers = {"Content-Type": "application/json"}

            requests.post(self.webhook_url, headers=headers, data=json.dumps(discord_message))

            self.logger.info("Alerting %s", alert.name)
            alert.notified = True
            alert.save()
