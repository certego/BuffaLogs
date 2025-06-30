import json

try:
    import requests
except ImportError:
    pass
from impossible_travel.alerting.base_alerting import BaseAlerting
from impossible_travel.models import Alert


class MicrosoftTeamsAlerting(BaseAlerting):
    """
    Concrete implementation of the BaseQuery class for MicrosoftTeamsAlerting.
    """

    def __init__(self, alert_config: dict):
        """
        Constructor for the MicrosoftTeams Alerter query object.
        """
        super().__init__()
        self.webhook_url = alert_config.get("webhook_url")

        if not self.webhook_url:
            self.logger.error("MicrosoftTeams Alerter configuration is missing required fields.")
            raise ValueError("MicrosoftTeams Alerter configuration is missing required fields.")

    def notify_alerts(self):
        """
        Execute the alerter operation.
        """
        alerts = Alert.objects.filter(notified=False)
        for alert in alerts:
            alert_title, alert_description = self.alert_message_formatter(alert)

            message_card = {
                "@type": "MessageCard",
                "@context": "http://schema.org/extensions",
                "themeColor": "FF0000",
                "title": alert_title,
                "text": alert_description,
            }
            try:
                resp = requests.post(
                    self.webhook_url,
                    headers={"Content-Type": "application/json"},
                    data=json.dumps(message_card),
                )
                resp.raise_for_status()
                self.logger.info(f"MicrosoftTeams alert sent: {alert.name}")
                alert.notified = True
                alert.save()
            except requests.RequestException as e:
                self.logger.exception(f"MicrosoftTeams alert failed for {alert.name}: {str(e)}")
