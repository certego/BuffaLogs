import requests
from impossible_travel.alerting.base_alerting import BaseAlerting
from impossible_travel.models import Alert


class TelegramAlerting(BaseAlerting):
    """
    Concrete implementation of the BaseQuery class for TelegramAlerting.
    """

    def __init__(self, alert_config: dict):
        """
        Constructor for the Telegram Alerter query object.
        """
        super().__init__()
        BOT_TOKEN = alert_config.get("bot_token")
        self.chat_ids = alert_config.get("chat_ids")  # only specific chat ids get alerts
        self.url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

        if not BOT_TOKEN or not self.chat_ids:
            self.logger.error("Telegram Alerter configuration is missing required fields.")
            raise ValueError("Telegram Alerter configuration is missing required fields.")

    def notify_alerts(self):
        """
        Execute the alerter operation.
        """
        alerts = Alert.objects.filter(notified=False)
        for alert in alerts:
            alert_msg = (
                f"Login Anomaly Alert: {alert.name}\nDear user,\n\nAn unusual login activity has been detected:\n\n{alert.description}\n\nStay Safe,\nBuffalogs"
            )
            try:
                # sending alerts to all the trusted chat ids
                for chat_id in self.chat_ids:
                    payload = {"chat_id": chat_id, "text": alert_msg}
                    resp = requests.post(self.url, json=payload)
                    resp.raise_for_status()

                self.logger.info(f"Telegram alert sent: {alert.name}")
                alert.notified = True
                alert.save()
            except requests.RequestException as e:
                self.logger.error(f"Telegram alert failed for {alert.name}: {str(e)}")
