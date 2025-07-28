from unittest.mock import MagicMock, patch

import requests
from django.test import TestCase

from impossible_travel.alerting.base_alerting import BaseAlerting
from impossible_travel.alerting.telegram_alerting import TelegramAlerting
from impossible_travel.models import Alert, Login, User


class TestTelegramAlerting(TestCase):
    def setUp(self):
        """Set up test data before running tests."""

        self.telegram_config = BaseAlerting.read_config("telegram")
        self.telegram_alerting = TelegramAlerting(self.telegram_config)

        # Create a dummy user
        self.user = User.objects.create(username="testuser")
        Login.objects.create(user=self.user, id=self.user.id)

        # Create an alert
        self.alert = Alert.objects.create(
            name="Imp Travel",
            user=self.user,
            notified_status={"telegram": False},
            description="Impossible travel detected",
            login_raw_data={},
        )

    @patch("requests.post")
    def test_send_alert(self, mock_post):
        """Doesn't actually sends the Alert,a mock request is sent"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        self.telegram_alerting.notify_alerts()

        # url expected where request made
        expected_url = f"https://api.telegram.org/bot{self.telegram_config['bot_token']}/sendMessage"
        expected_alert_title, expected_alert_description = (
            BaseAlerting.alert_message_formatter(self.alert)
        )
        expected_alert_msg = (
            expected_alert_title + "\n\n" + expected_alert_description
        )

        # Check that requests.post was called twice for each alert (1 chat_ids x 1 alerts = 1)
        self.assertEqual(mock_post.call_count, 1)

        # calls made
        calls = [
            (
                (expected_url,),
                {
                    "json": {
                        "chat_id": f"{self.telegram_config['chat_ids'][0]}",
                        "text": expected_alert_msg,
                    }
                },
            )
        ]

        mock_post.assert_has_calls(calls, any_order=True)

    @patch("requests.post")
    def test_no_alerts(self, mock_post):
        """Test that no alerts are sent when there are no alerts to notify"""
        for alert in Alert.objects.all():
            alert.notified_status["telegram"] = True
            alert.save()
        self.telegram_alerting.notify_alerts()
        self.assertEqual(mock_post.call_count, 0)

    def test_improper_config(self):
        """Test that an error is raised if the configuration is not correct"""
        with self.assertRaises(ValueError):
            TelegramAlerting({})

    @patch("requests.post")
    def test_alert_network_failure(self, mock_post):
        """Test that alert is not marked as notified if there are any Network Fails"""
        # Simulate network/API failure
        mock_post.side_effect = requests.RequestException()

        self.telegram_alerting.notify_alerts()

        # Reload the alert from DB to check its state
        alert = Alert.objects.get(pk=self.alert.pk)
        self.assertFalse(alert.notified_status["telegram"])
