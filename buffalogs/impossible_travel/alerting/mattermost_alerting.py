import requests
from impossible_travel.alerting.base_alerting import BaseAlerting
from impossible_travel.models import Alert


class MattermostAlerting(BaseAlerting):
    """
    Concrete implementation of the BaseQuery class for MattermostAlerting.
    """

    def __init__(self, alert_config: dict):
        """
        Constructor for the Mattermost Alerter query object.
        """
        super().__init__()
        self.webhook_url = alert_config.get("webhook_url")
        self.username = alert_config.get("username")

        if not self.webhook_url or not self.username:
            self.logger.error("Mattermost Alerter configuration is missing required fields.")
            raise ValueError("Mattermost Alerter configuration is missing required fields.")

    def notify_alerts(self):
        """
        Execute the alerter operation.
        """
        alerts = Alert.objects.filter(notified=False)

        for alert in alerts:
            alert_title, alert_description = self.alert_message_formatter(alert)
            alert_msg = alert_title + "\n\n" + alert_description

            try:
                message = {
                    "text": alert_msg,
                    "username": self.username,
                }

                resp = requests.post(self.webhook_url, json=message)
                resp.raise_for_status()
                self.logger.info(f"Mattermost alert sent: {alert.name}")
                alert.notified = True
                alert.save()
            except requests.RequestException as e:
                self.logger.exception(f"Mattermost alert failed for {alert.name}: {str(e)}")
