import requests
from impossible_travel.alerting.base_alerting import BaseAlerting
from impossible_travel.models import Alert


class RocketChatAlerting(BaseAlerting):
    """
    Implementation of the BaseAlerting class for RocketChat Alerts.
    """

    def __init__(self, alert_config: dict):
        """
        Initialize the RocketChat Alerting class.
        """
        super().__init__()
        # here we can access the alert_config to get the configuration for the alerter
        self.webhook_url = alert_config.get("webhook_url")
        self.channel = alert_config.get("channel")
        self.username = alert_config.get("username")

    def notify_alerts(self):
        """
        Execute the alerter operation.
        """
        alerts = Alert.objects.filter(notified=False)
        for alert in alerts:
            # the alert message to send
            alert_msg = f"Dear user,\n\nAn unusual login activity has been detected:\n\n{alert.description}\n\nStay Safe,\nBuffalogs"

            rocketchat_message = {"text": alert_msg, "username": self.username, "channel": self.channel}

            requests.post(self.webhook_url, data=rocketchat_message)

            self.logger.info("Alerting %s", alert.name)
            alert.notified = True
            alert.save()
