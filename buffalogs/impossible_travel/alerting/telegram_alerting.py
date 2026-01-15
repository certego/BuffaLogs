try:
    import requests
except ImportError:
    pass
from collections import defaultdict

import backoff
from django.db.models import Q
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
        self.chat_ids = alert_config.get(
            "chat_ids"
        )  # only specific chat ids get alerts
        self.url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

        if not BOT_TOKEN or not self.chat_ids:
            self.logger.error(
                "Telegram Alerter configuration is missing required fields."
            )
            raise ValueError(
                "Telegram Alerter configuration is missing required fields."
            )

    @backoff.on_exception(backoff.expo, requests.RequestException, max_tries=5, base=2)
    def send_message(self, alert, alert_title=None, alert_description=None):
        if alert_title is None and alert_description is None and alert:
            alert_title, alert_description = self.alert_message_formatter(alert)

        alert_msg = alert_title + "\n\n" + alert_description

        # sending alerts to all the trusted chat ids
        for chat_id in self.chat_ids:
            payload = {"chat_id": chat_id, "text": alert_msg}
            resp = requests.post(self.url, json=payload)
            resp.raise_for_status()
            return resp

    def send_scheduled_summary(
        self, start_date, end_date, total_alerts, user_breakdown, alert_breakdown
    ):
        summary_title, summary_description = self.alert_message_formatter(
            alert=None,
            template_path="alert_template_summary.jinja",
            start_date=start_date,
            end_date=end_date,
            total_alerts=total_alerts,
            user_breakdown=user_breakdown,
            alert_breakdown=alert_breakdown,
        )

        try:
            self.send_message(
                alert=None,
                alert_title=summary_title,
                alert_description=summary_description,
            )
            self.logger.info(f"Telegram Summary Sent From: {start_date} To: {end_date}")
        except requests.RequestException as e:
            self.logger.exception(f"Telegram Summary Notification Failed: {str(e)}")

    def notify_alerts(self, start_date=None, end_date=None):
        """
        Execute the alerter operation.
        """
        alerts = Alert.objects.filter(
            (
                Q(notified_status__telegram=False)
                | ~Q(notified_status__has_key="telegram")
            )
        )
        if start_date is not None and end_date is not None:
            alerts = Alert.objects.filter(
                (
                    Q(notified_status__telegram=False)
                    | ~Q(notified_status__has_key="telegram")
                )
                & Q(created__range=(start_date, end_date))
            )

        grouped = defaultdict(list)
        for alert in alerts:
            key = (alert.user.username, alert.name)
            grouped[key].append(alert)

        for (username, alert_name), group_alerts in grouped.items():
            if len(group_alerts) == 1:
                try:
                    alert = group_alerts[0]
                    self.send_message(alert=alert)
                    self.logger.info(f"Telegram alert sent: {alert.name}")
                    alert.notified_status["telegram"] = True
                    alert.save()
                except requests.RequestException as e:
                    self.logger.exception(
                        f"Telegram Notification Failed for {alert}: {str(e)}"
                    )

            else:
                alert = group_alerts[0]
                alert_title, alert_description = self.alert_message_formatter(
                    alert=alert,
                    template_path="alert_template_clubbed.jinja",
                    alerts=group_alerts,
                )
                try:
                    self.send_message(
                        alert=None,
                        alert_title=alert_title,
                        alert_description=alert_description,
                    )
                    self.logger.info(f"Clubbed Telegram Alert Sent: {alert_title}")

                    for a in group_alerts:
                        a.notified_status["telegram"] = True
                        a.save()
                except requests.RequestException as e:
                    self.logger.exception(
                        f"Clubbed Telegram Alert Failed for {group_alerts}: {str(e)}"
                    )
