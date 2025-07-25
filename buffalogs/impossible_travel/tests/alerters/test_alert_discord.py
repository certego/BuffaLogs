import json
from unittest.mock import MagicMock, patch

import requests
from django.test import TestCase
from impossible_travel.alerting.base_alerting import BaseAlerting
from impossible_travel.alerting.discord_alerting import DiscordAlerting
from impossible_travel.models import Alert, Login, User


class TestDiscordAlerting(TestCase):
    def setUp(self):
        """Set up test data before running tests."""

        self.discord_config = BaseAlerting.read_config("discord")
        self.discord_alerting = DiscordAlerting(self.discord_config)

        # Create a dummy user
        self.user = User.objects.create(username="testuser")
        Login.objects.create(user=self.user, id=self.user.id)

        # Create an alert
        self.alert = Alert.objects.create(
            name="Imp Travel", user=self.user, notified_status={"discord": False}, description="Impossible travel detected", login_raw_data={}
        )

    @patch("requests.post")
    def test_send_alert(self, mock_post):
        """Doesn't actually sends the Alert,a mock request is sent"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        self.discord_alerting.notify_alerts()

        expected_alert_title, expected_alert_description = BaseAlerting.alert_message_formatter(self.alert)

        expected_payload = {
            "username": self.discord_config["username"],
            "embeds": [
                {
                    "title": expected_alert_title,
                    "description": expected_alert_description,
                    "color": 16711680,
                }
            ],
        }

        mock_post.assert_called_once_with(
            self.discord_config["webhook_url"],
            headers={"Content-Type": "application/json"},
            data=json.dumps(expected_payload),
        )

    @patch("requests.post")
    def test_no_alerts(self, mock_post):
        """Test that no alerts are sent when there are no alerts to notify"""
        for alert in Alert.objects.all():
            alert.notified_status["discord"] = True
            alert.save()
        self.discord_alerting.notify_alerts()
        self.assertEqual(mock_post.call_count, 0)

    def test_improper_config(self):
        """Test that an error is raised if the configuration is not correct"""
        with self.assertRaises(ValueError):
            DiscordAlerting({})
