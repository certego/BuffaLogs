from unittest.mock import MagicMock, patch

from django.test import TestCase
from impossible_travel.alerting.telegram_alerting import TelegramAlerting
from impossible_travel.models import Alert, Login, User


class TestTelegramAlerting(TestCase):
    def setUp(self):
        """Set up test data before running tests."""

        self.telegram_config = {"bot_name": "Buffalogs Alerter Bot", "bot_username": "buffalogs_alerter_bot", "bot_token": "BOT_TOKEN", "chat_ids": ["CHAT_ID"]}
        self.tg_alerting = TelegramAlerting(self.telegram_config)

        # Create a dummy user
        self.user = User.objects.create(username="testuser")
        Login.objects.create(user=self.user, id=self.user.id)

        # Create an alert
        self.alert = Alert.objects.create(name="Imp Travel", user=self.user, notified=False, description="Impossible travel detected", login_raw_data={})

    @patch("requests.post")
    def test_send_alert(self, mock_post):
        """Doesn't actually sends the Alert,a mock request is sent"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        self.tg_alerting.notify_alerts()

        # url expected where request made
        expected_url = "https://api.telegram.org/botBOT_TOKEN/sendMessage"

        # Check that requests.post was called twice for each alert (1 chat_ids x 1 alerts = 1)
        self.assertEqual(mock_post.call_count, 1)

        # calls made
        calls = [
            (
                (expected_url,),
                {
                    "json": {
                        "chat_id": "CHAT_ID",
                        "text": "Login Anomaly Alert: Imp Travel\nDear user,\n\nAn unusual login activity has been detected:\n\nImpossible travel detected\n\nStay Safe,\nBuffalogs",
                    }
                },
            )
        ]

        mock_post.assert_has_calls(calls, any_order=True)

    def test_send_actual_alert(self):
        """Sending actual alert message to the chat"""
        self.tg_alerting.notify_alerts()
