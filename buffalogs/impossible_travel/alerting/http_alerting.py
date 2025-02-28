import requests
from impossible_travel.alerting.base_alerting import BaseAlerting
from impossible_travel.models import Alert


class HttpAlerting(BaseAlerting):
    """
    Concrete implementation of the BaseQuery class for DummyAlerting.
    """

    def __init__(self, alert_config: dict):
        """
        Constructor for the Http Alerter query object.
        """
        super().__init__()
        self.url = alert_config.get("endpoint_url")
        self.headers = alert_config.get("headers", {})
        self.timeout = alert_config.get("timeout", 10)

        if not self.url:
            raise ValueError("HTTP Alerter requires a 'url' configuration")
        self.logger.info("Initialized HTTP Alerter with URL: %s", self.url)

    def notify_alerts(self):
        """
        Execute the alerter operation.
        """
        alerts = Alert.objects.filter(notified=False)
        for alert in alerts:
            try:
                message = {
                    "user": alert.user.username,
                    "alert_name": alert.name,
                    "description": alert.description,
                    "created": alert.created,
                }
                response = requests.post(
                    self.url,
                    json=message,
                    headers=self.headers,
                    timeout=self.timeout,
                )
                response.raise_for_status()
                self.logger.info("Alerting %s", alert.name)
                alert.notified = True
                alert.save()
            except Exception as e:
                self.logger.error("Failed to send alert %s: %s", alert.name, str(e))
