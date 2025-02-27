import requests
from impossible_travel.alerting.base_alerting import BaseAlerting
from impossible_travel.models import Alert


class TelegramAlerting(BaseAlerting):
    def __init__(self, alert_config: dict):
        """
        Constructor for the Telegram Alerter query object.
        """
        super().__init__()
        # here we can access the alert_config to get the configuration for the alerter
        BOT_TOKEN = alert_config.get("bot_token")
        self.chat_ids = alert_config.get("chat_ids")  # only specific chat ids get alerts
        self.url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    def notify_alerts(self):
        """
        Execute the alerter operation.
        """
        alerts = Alert.objects.filter(notified=False)
        for alert in alerts:
            # in a real alerters, this would be the place to send the alert
            alert_msg = (
                f"Login Anomaly Alert: {alert.name}\nDear user,\n\nAn unusual login activity has been detected:\n\n{alert.description}\n\nStay Safe,\nBuffalogs"
            )

            # sending alerts to all the trusted chat ids
            for chat_id in self.chat_ids:
                payload = {"chat_id": chat_id, "text": alert_msg}
                requests.post(self.url, json=payload)

            self.logger.info("Alerting %s", alert.name)
            alert.notified = True
            alert.save()
