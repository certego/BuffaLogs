import json

try:
    import requests
except ImportError:
    pass
from collections import defaultdict

import backoff
from django.db.models import Q
from impossible_travel.alerting.base_alerting import BaseAlerting
from impossible_travel.models import Alert


class DiscordAlerting(BaseAlerting):
    """
    Concrete implementation of the BaseQuery class for DiscordAlerting.
    """

    def __init__(self, alert_config: dict):
        """
        Constructor for the Discord Alerter query object.
        """
        super().__init__()
        self.webhook_url = alert_config.get("webhook_url")
        self.username = alert_config.get("username")

        if not self.webhook_url or not self.username:
            self.logger.error("Discord Alerter configuration is missing required fields.")
            raise ValueError("Discord Alerter configuration is missing required fields.")

    @backoff.on_exception(backoff.expo, requests.RequestException, max_tries=5, base=2)
    def send_message(self, alert, alert_title=None, alert_description=None):
        if alert_title is None and alert_description is None and alert:
            alert_title, alert_description = self.alert_message_formatter(alert)

        alert_msg = {
            "username": self.username,
            "embeds": [
                {
                    "title": alert_title,
                    "description": alert_description,
                    "color": 16711680,
                }
            ],  # red
        }
        headers = {"Content-Type": "application/json"}

        resp = requests.post(self.webhook_url, headers=headers, data=json.dumps(alert_msg))
        resp.raise_for_status()
        return resp

    def send_scheduled_summary(self, start_date, end_date, total_alerts, user_breakdown, alert_breakdown):
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
            self.logger.info(f"Discord Summary Sent From: {start_date} To: {end_date}")
        except requests.RequestException as e:
            self.logger.exception(f"Discord Summary Notification Failed: {str(e)}")

    def notify_alerts(self, start_date=None, end_date=None):
        """
        Execute the alerter operation.
        """
        alerts = Alert.objects.filter((Q(notified_status__discord=False) | ~Q(notified_status__has_key="discord")))
        if start_date is not None and end_date is not None:
            alerts = Alert.objects.filter(
                (Q(notified_status__discord=False) | ~Q(notified_status__has_key="discord")) & Q(created__range=(start_date, end_date))
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
                    self.logger.info(f"Discord alert sent: {alert.name}")
                    alert.notified_status["discord"] = True
                    alert.save()
                except requests.RequestException as e:
                    self.logger.exception(f"Discord Notification Failed for {alert}: {str(e)}")

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
                    self.logger.info(f"Clubbed Discord Alert Sent: {alert_title}")

                    for a in group_alerts:
                        a.notified_status["discord"] = True
                        a.save()
                except requests.RequestException as e:
                    self.logger.exception(f"Clubbed Discord Alert Failed for {group_alerts}: {str(e)}")
