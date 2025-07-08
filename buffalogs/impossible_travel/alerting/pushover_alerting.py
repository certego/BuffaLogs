try:
    import requests
except ImportError:
    pass
from django.db.models import Q
from impossible_travel.alerting.base_alerting import BaseAlerting
from impossible_travel.models import Alert


class PushoverAlerting(BaseAlerting):
    """
    Concrete implementation of the BaseQuery class for PushoverAlerting.
    """

    def __init__(self, alert_config: dict):
        """
        Constructor for the Pushover Alerter query object.
        """
        super().__init__()
        self.api_key = alert_config.get("api_key")
        self.user_key = alert_config.get("user_key")

        if not self.api_key or not self.user_key:
            self.logger.error("Pushover Alerter configuration is missing required fields.")
            raise ValueError("Pushover Alerter configuration is missing required fields.")

    def notify_alerts(self):
        """
        Execute the alerter operation.
        """
        alerts = Alert.objects.filter(Q(notified_status__pushover=False) | ~Q(notified_status__has_key="pushover"))
        for alert in alerts:
            alert_title, alert_description = self.alert_message_formatter(alert)
            alert_msg = alert_title + "\n\n" + alert_description

            payload = {"token": self.api_key, "user": self.user_key, "message": alert_msg}
            try:
                resp = requests.post("https://api.pushover.net/1/messages.json", data=payload)
                resp.raise_for_status()
                self.logger.info(f"Pushover alert sent: {alert.name}")
                alert.notified_status["pushover"] = True
                alert.save()
            except requests.RequestException as e:
                self.logger.exception(f"Pushover alert failed for {alert.name}: {str(e)}")
