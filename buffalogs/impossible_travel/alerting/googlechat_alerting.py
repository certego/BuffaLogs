import requests
from impossible_travel.alerting.base_alerting import BaseAlerting
from impossible_travel.models import Alert


class GoogleChatAlerting(BaseAlerting):
    """
    Implementation of the BaseAlerting class for GoogleChat Alerts.
    """

    def __init__(self, alert_config: dict):
        """
        Initialize the GoogleChat Alerting class.
        """
        super().__init__()
        self.webhook_url = alert_config.get("webhook_url")

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

                response = requests.post(self.webhook_url, json=message)

                self.logger.info("Alert:%s sent to GoogleChat", alert.name)
                alert.notified = True
                alert.save()

        except Exception as e:
            self.logger.error(f"Error sending GoogleChat alert: {str(e)}")
