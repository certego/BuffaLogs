import requests
from impossible_travel.alerting.base_alerting import BaseAlerting
from impossible_travel.models import Alert


class GoogleChatAlerting(BaseAlerting):
    """
    Concrete implementation of the BaseQuery class for GoogleChatAlerting.
    """

    def __init__(self, alert_config: dict):
        """
        Constructor for the GoogleChat Alerter query object.
        """
        super().__init__()
        self.webhook_url = alert_config.get("webhook_url")
        if not self.webhook_url:
            self.logger.error("GoogleChat Alerter configuration is missing required fields.")
            raise ValueError("GoogleChat Alerter configuration is missing required fields.")

    def notify_alerts(self):
        """
        Execute the alerter operation.
        """
        alerts = Alert.objects.filter(notified=False)

        for alert in alerts:
            try:
                message = {
                    "cards": [
                        {
                            "header": {"title": "Login Anomaly Alert", "subtitle": alert.name},
                            "sections": [
                                {
                                    "widgets": [
                                        {
                                            "textParagraph": {
                                                "text": f"Dear user,\n\nAn unusual login activity has been detected:\n\n{alert.description}\n\nStay Safe,\nBuffalogs"
                                            }
                                        }
                                    ]
                                }
                            ],
                        }
                    ]
                }

                resp = requests.post(self.webhook_url, json=message)
                resp.raise_for_status()
                self.logger.info(f"GoogleChat alert sent: {alert.name}")
                alert.notified = True
                alert.save()

            except requests.RequestException as e:
                self.logger.exception(f"GoogleChat alert failed for {alert.name}: {str(e)}")
