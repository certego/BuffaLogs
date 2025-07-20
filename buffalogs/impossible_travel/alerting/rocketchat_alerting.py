try:
    import requests
except ImportError:
    pass
from django.db.models import Q
from impossible_travel.alerting.base_alerting import BaseAlerting
from impossible_travel.models import Alert


class RocketChatAlerting(BaseAlerting):
    """
    Concrete implementation of the BaseQuery class for RocketChatAlerting.
    """

    def __init__(self, alert_config: dict):
        """
        Constructor for the RocketChat Alerter query object.
        """
        super().__init__()
        self.webhook_url = alert_config.get("webhook_url")
        self.channel = alert_config.get("channel")
        self.username = alert_config.get("username")

        if not self.webhook_url or not self.channel or not self.username:
            self.logger.error("RocketChat Alerter configuration is missing required fields.")
            raise ValueError("RocketChat Alerter configuration is missing required fields.")

    def notify_alerts(self):
        """
        Execute the alerter operation.
        """
        alerts = Alert.objects.filter(Q(notified_status__rocketchat=False) | ~Q(notified_status__has_key="rocketchat"))
        for alert in alerts:
            alert_title, alert_description = self.alert_message_formatter(alert)
            alert_msg = alert_title + "\n\n" + alert_description

            rocketchat_message = {"text": alert_msg, "username": self.username, "channel": self.channel}
            try:
                resp = requests.post(self.webhook_url, data=rocketchat_message)
                resp.raise_for_status()
                self.logger.info(f"RocketChat alert sent: {alert.name}")
                alert.notified_status["rocketchat"] = True
                alert.save()
            except requests.RequestException as e:
                self.logger.exception(f"RocketChat alert failed for {alert.name}: {str(e)}")
