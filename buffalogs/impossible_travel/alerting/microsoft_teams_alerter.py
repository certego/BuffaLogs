import json

import requests
from impossible_travel.alerting.base_alerting import BaseAlerting
from impossible_travel.models import Alert


class MicrosoftTeamsAlerting(BaseAlerting):
    """
    Concrete implementation of the BaseQuery class for MicrosoftTeams.
    """

    def __init__(self, alert_config: dict):
        """
        Constructor for the MicrosoftTeams Alerter query object.
        """
        super().__init__()
        self.webhook_url = alert_config.get("webhook_url")
        if not self.webhook_url:
            raise ValueError("Microsoft Teams webhook URL is missing in configuration.")

    def notify_alerts(self):
        """
        Execute the alerter operation.
        """
        try:
            alerts = Alert.objects.filter(notified=False)
            for alert in alerts:
                message_card = {
                    "@type": "MessageCard",
                    "@context": "http://schema.org/extensions",
                    "themeColor": "FF0000",
                    "title": f"Security Alert: {alert.name}",
                    "text": f"{alert.description}\n\nstay safe, BuffaLogs",
                }

                response = requests.post(self.webhook_url, headers={"Content-Type": "application/json"}, data=json.dumps(message_card))

                response.raise_for_status()
                self.logger.info("Alerting %s", alert.name)
                alert.notified = True
                alert.save()

        except requests.exceptions.RequestException as e:
            self.logger.error(f"API error: {str(e)}")
