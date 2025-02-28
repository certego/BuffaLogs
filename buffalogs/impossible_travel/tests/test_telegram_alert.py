from unittest.mock import patch

import requests
from django.test import TestCase
from impossible_travel.alerting.telegram_alerting import TelegramAlerting
from impossible_travel.models import Alert, User


class TestTelegramAlerting(TestCase):

    def setUp(self):
        # Create a test user and alert
        self.user = User.objects.create(username="test_user")
        self.alert = Alert.objects.create(
            user=self.user,
            name="New Country",
            description="Unusual login activity detected",
            notified=False,
            login_raw_data={},
        )
        self.alert_config = {
            "bot_token": "test_bot_token",
            "chat_id": "test_chat_id",
            "api_base_url": "https://api.telegram.org",
        }

    @patch("requests.post")
    def test_notify_alerts_success(self, mock_post):
        # Mock successful API response
        mock_post.return_value.status_code = 200
        mock_post.return_value.raise_for_status.return_value = None

        alerter = TelegramAlerting(self.alert_config)
        alerter.notify_alerts()

        # Refresh the alert from the database
        self.alert.refresh_from_db()

        # Assert the alert is marked as notified
        self.assertTrue(self.alert.notified)

        # Verify the correct API endpoint and parameters were used
        expected_url = (
            f"{self.alert_config['api_base_url']}/bot"
            f"{self.alert_config['bot_token']}/sendMessage"
        )
        
        mock_post.assert_called_once_with(
            expected_url,
            json={
                "chat_id": self.alert_config["chat_id"],
                "text": alerter._format_message(self.alert),
                "parse_mode": "Markdown",
            },
            timeout=10,
        )

    @patch("requests.post")
    def test_notify_alerts_failure(self, mock_post):
        # Simulate a request exception
        mock_post.side_effect = requests.exceptions.RequestException("Connection Error")

        alerter = TelegramAlerting(self.alert_config)
        alerter.notify_alerts()

        # Refresh the alert from the database
        self.alert.refresh_from_db()

        # Assert the alert remains not notified
        self.assertFalse(self.alert.notified)

        # Verify the API was called (even though it failed)
        expected_url = (
            f"{self.alert_config['api_base_url']}/bot"
            f"{self.alert_config['bot_token']}/sendMessage"
        )
        mock_post.assert_called_once_with(
            expected_url,
            json={
                "chat_id": self.alert_config["chat_id"],
                "text": alerter._format_message(self.alert),
                "parse_mode": "Markdown",
            },
            timeout=10,
        )
