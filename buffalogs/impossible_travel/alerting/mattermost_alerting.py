import requests
from impossible_travel.alerting.base_alerting import BaseAlerting
from impossible_travel.models import Alert


class MattermostAlerting(BaseAlerting):
    """
    Implementation of the BaseAlerting class for Mattermost Alerts.
    """

    def __init__(self, alert_config: dict):
        """
        Initialize the Mattermost Alerting class.
        """
        super().__init__()
        self.webhook_url = alert_config.get("webhook_url")
        self.username = alert_config.get("username")

    def notify_alerts(self):
        """
        Execute the alerter operation.
        """
        alerts = Alert.objects.filter(notified=False)
        if not alerts.exists():
            return

        try:
            for alert in alerts:
                message = {
                    "text": f"Dear user,\n\nAn unusual login activity has been detected:\n\n{alert.description}\n\nStay Safe,\nBuffalogs",
                    "username": self.username,
                }

                response = requests.post(self.webhook_url, json=message)

                self.logger.info("Alert:%s sent to Mattermost", alert.name)
                alert.notified = True
                alert.save()

        except Exception as e:
            self.logger.error(f"Error sending Mattermost alert: {str(e)}")
