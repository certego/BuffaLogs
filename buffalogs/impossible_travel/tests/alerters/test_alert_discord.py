import json
from unittest.mock import MagicMock, patch

import requests
from django.test import TestCase
from impossible_travel.alerting.base_alerting import BaseAlerting
from impossible_travel.alerting.discord_alerting import DiscordAlerting
from impossible_travel.models import Alert, Login, User


class TestDiscordAlerting(TestCase):
    @classmethod
    def setUpTestData(cls):
        """Set up test data once for all tests."""
        cls.discord_config = BaseAlerting.read_config("discord")
        cls.discord_alerting = DiscordAlerting(cls.discord_config)

        cls.user = User.objects.create(username="testuser")
        Login.objects.create(user=cls.user, id=cls.user.id)

        cls.alert = Alert.objects.create(
            name="Imp Travel",
            user=cls.user,
            notified_status={"discord": False},
            description="Impossible travel detected",
            login_raw_data={},
        )

    @patch("requests.post")
    def test_send_alert(self, mock_post):
        """Test that a properly formed alert is sent via POST"""
        mock_post.return_value = MagicMock(status_code=200)

        self.discord_alerting.notify_alerts()

        expected_title, expected_description = BaseAlerting.alert_message_formatter(self.alert)
        expected_payload = {
            "username": self.discord_config["username"],
            "embeds": [
                {
                    "title": expected_title,
                    "description": expected_description,
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

    @patch("requests.post")
    def test_alert_network_failure(self, mock_post):
        """Test that alert is not marked as notified if there are any Network Fails"""
        # Simulate network/API failure
        mock_post.side_effect = requests.RequestException()

        self.discord_alerting.notify_alerts()

        # Reload the alert from DB to check its state
        alert = Alert.objects.get(pk=self.alert.pk)
        self.assertFalse(alert.notified_status["discord"])
