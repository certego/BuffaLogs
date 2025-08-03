try:
    import requests
except ImportError:
    pass
from collections import defaultdict
from datetime import timedelta

import backoff
from django.db.models import Q
from django.utils import timezone
from impossible_travel.alerting.base_alerting import BaseAlerting
from impossible_travel.models import Alert


class SlackAlerting(BaseAlerting):
    """
    Concrete implementation of the BaseQuery class for SlackAlerting.
    """

    def __init__(self, alert_config: dict):
        """
        Constructor for the Slack Alerter query object.
        """
        super().__init__()
        self.webhook_url = alert_config.get("webhook_url")

        if not self.webhook_url:
            self.logger.error("Slack Alerter configuration is missing required fields.")
            raise ValueError("Slack Alerter configuration is missing required fields.")

    @backoff.on_exception(backoff.expo, requests.RequestException, max_tries=5, base=2)
    def send_message(self, alert):
        alert_title, alert_description = self.alert_message_formatter(alert)
        alert_msg = {
            "attachments": [
                {
                    "title": alert_title,
                    "text": alert_description,
                    "color": "#ff0000",  # red color
                }
            ]
        }

        resp = requests.post(self.webhook_url, json=alert_msg, headers={"Content-Type": "application/json"})
        resp.raise_for_status()
        self.logger.info(f"Slack alert sent: {alert.name}")
        alert.notified_status["slack"] = True
        alert.save()

        return resp

    def notify_alerts(self):
        """
        Execute the alerter operation.
        """
        time_threshold = timezone.now() - timedelta(minutes=5)
        alerts = Alert.objects.filter((Q(notified_status__slack=False) | ~Q(notified_status__has_key="slack")) & Q(created__gte=time_threshold))

        grouped = defaultdict(list)
        for alert in alerts:
            key = (alert.user.username, alert.name)
            grouped[key].append(alert)

        for (username, alert_name), group_alerts in grouped.items():
            try:
                if len(group_alerts) == 1:
                    self.send_message(group_alerts[0])
                else:
                    alert = group_alerts[0]
                    alert_title, alert_description = self.alert_message_formatter(
                        alert=alert, template_path="alert_template_clubbed.jinja", alerts=group_alerts
                    )
                    alert_msg = {
                        "attachments": [
                            {
                                "title": alert_title,
                                "text": alert_description,
                                "color": "#ff0000",
                            }
                        ]
                    }
                    resp = requests.post(self.webhook_url, json=alert_msg, headers={"Content-Type": "application/json"})
                    resp.raise_for_status()
                    self.logger.info(f"Clubbed Slack alert sent: {alert_title}")

                    for a in group_alerts:
                        a.notified_status["slack"] = True
                        a.save()
            except requests.RequestException as e:
                self.logger.exception(f"Slack alert failed for {alert.name}: {str(e)}")
