import json
from typing import Any, Dict

import requests

from .base_alerting import BaseAlerting


class SlackAlerter(BaseAlerting):
    """Slack alerter for BuffaLogs impossible travel detection."""

    def __init__(self, config):
        super().__init__()
        self.webhook_url = config.get("webhook_url")
        if not self.webhook_url:
            raise ValueError("Slack webhook URL is required")
        self.channel = config.get("channel", "#general")
        self.alerts_data = []

    def format_message(self, alert_data):
        """Format the alert data into a Slack message."""
        return {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "🚨 Impossible Travel Alert",
                    },
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*User:* {alert_data.get('user', 'Unknown')}",
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Time:* {alert_data.get('timestamp', 'Unknown')}",
                        },
                    ],
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Location 1:* {alert_data.get('location1', 'Unknown')}",
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Location 2:* {alert_data.get('location2', 'Unknown')}",
                        },
                    ],
                },
            ]
        }

    def notify_alerts(self):
        """Implementation of the abstract method to send alerts."""
        success = True
        for alert_data in self.alerts_data:
            if not self.send_alert(alert_data):
                success = False
        return success

    def send_alert(self, alert_data):
        """Send alert to Slack channel."""
        try:
            message = self.format_message(alert_data)
            response = requests.post(
                self.webhook_url,
                json=message,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            return True
        except Exception as e:
            self.logger.error(f"Failed to send Slack alert: {str(e)}")
            return False
