import requests
from impossible_travel.alerting.base_alerting import BaseAlerting
from impossible_travel.models import Alert


class TelegramAlerting(BaseAlerting):
    """
    Implementation of the BaseAlerting class for Telegram Alerts.
    """

    def __init__(self, alert_config: dict):
        """
        Constructor for the Telegram Alerter query object.
        """
        super().__init__()
        self.telegram_config = alert_config
        self.bot_token = self.telegram_config.get("bot_token")
        self.chat_id = self.telegram_config.get("chat_id")
        self.api_base_url = self.telegram_config.get("api_base_url")

    def notify_alerts(self):
        """
        Execute the alerter operation.
        """
        alerts = Alert.objects.filter(notified=False)

        if not alerts.exists():
            self.logger.info("No pending alerts to notify")
            return

        for alert in alerts:
            success = self._post_telegram_message(alert)
            if success:
                self.logger.info("Alerting %s", alert.name)
                alert.notified = True
                alert.save()
            else:
                self.logger.warning(f"Failed to notify alert {alert.id}")

    def _format_message(self, alert):
        """Formats an alert message for Telegram using Markdown."""
        return (
            f"**Dear {alert.user.username},**\n\n"
            f"We have detected *unusual login activity*. Please review the details below:\n\n"  # noqa: E501
            f"**Details:** {alert.description}\n"
            f"**Time:** {alert.created.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"Thank you,\n"
            f"Your BuffaLogs-Security Team"
        )

    def _post_telegram_message(self, alert):
        """Posts an alert message to Telegram."""
        message = self._format_message(alert)
        url = f"{self.api_base_url}/bot{self.bot_token}/sendMessage"
        try:
            response = requests.post(
                url,
                json={
                    "chat_id": self.chat_id,
                    "text": message,
                    "parse_mode": "Markdown",
                },
                timeout=10,
            )
            response.raise_for_status()
            return True
        except Exception as e:
            self.logger.error(
                f"Telegram notification failed for alert {alert.id}: {str(e)}"
            )
            return False