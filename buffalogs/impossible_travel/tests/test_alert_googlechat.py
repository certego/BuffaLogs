import json
from unittest.mock import MagicMock, patch

from django.test import TestCase
from impossible_travel.alerting.googlechat_alerting import GoogleChatAlerting
from impossible_travel.models import Alert, Login, User


class TestGoogleChatAlerting(TestCase):
    def setUp(self):
        """Set up test data before running tests."""

        self.googlechat_config = {"webhook_url": "https://chat.googleapis.com/YOUR_WEBHOOK_URL"}
        self.googlechat_alerting = GoogleChatAlerting(self.googlechat_config)

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

        self.googlechat_alerting.notify_alerts()

        expected_payload = {
            "cards": [
                {
                    "header": {"title": "Login Anomaly Alert", "subtitle": "Imp Travel"},
                    "sections": [
                        {
                            "widgets": [
                                {
                                    "textParagraph": {
                                        "text": "Dear user,\n\nAn unusual login activity has been detected:\n\nImpossible travel detected\n\nStay Safe,\nBuffalogs"
                                    }
                                }
                            ]
                        }
                    ],
                }
            ]
        }

        mock_post.assert_called_once_with(
            "https://chat.googleapis.com/YOUR_WEBHOOK_URL",
            json=expected_payload,
        )

    def test_send_actual_alert(self):
        # Sending actual alert message to the chat
        self.googlechat_alerting.notify_alerts()
