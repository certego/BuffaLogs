import requests
from impossible_travel.alerting.base_alerting import BaseAlerting
from impossible_travel.models import Alert


class PushoverAlerting(BaseAlerting):
    """
    Concrete implementation of the BaseQuery class for Pushover.
    """

    def __init__(self, alert_config: dict):
        """
        Constructor for the Pushover Alerter query object.
        """
        super().__init__()
        # here we can access the alert_config to get the configuration for the alerter
        self.api_key = alert_config.get("api_key")
        self.user_key = alert_config.get("user_key")

    def notify_alerts(self):
        """
        Execute the alerter operation.
        """
        alerts = Alert.objects.filter(notified=False)
        for alert in alerts:
            # the alert message to send
            alert_msg = (
                f"Login Anomaly Alert: {alert.name}\nDear user,\n\nAn unusual login activity has been detected:\n\n{alert.description}\n\nStay Safe,\nBuffalogs"
            )

            # create the payload to send
            payload = {"token": self.api_key, "user": self.user_key, "message": alert_msg}

            # post the request to pushover
            requests.post("https://api.pushover.net/1/messages.json", data=payload)

            self.logger.info("Alerting %s", alert.name)
            alert.notified = True
            alert.save()
