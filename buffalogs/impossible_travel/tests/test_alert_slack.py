from unittest.mock import MagicMock, patch

from django.test import TestCase
from impossible_travel.alerting.slack_alerting import SlackAlerting
from impossible_travel.models import Alert, Login, User


class TestSlackAlerting(TestCase):
    def setUp(self):
        """Set up test data before running tests."""

        self.slack_config = {"webhook_url": "https://hooks.slack.com/services/WEBHOOK"}
        self.slack_alerting = SlackAlerting(self.slack_config)

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

        self.slack_alerting.notify_alerts()

        expected_payload = {
            "attachments": [
                {
                    "title": "Login Anomaly Alert: Imp Travel",
                    "text": "Dear user,\n\nAn unusual login activity has been detected:\n\nImpossible travel detected\n\nStay Safe,\nBuffalogs",
                    "color": "#ff0000",
                }
            ]
        }

        mock_post.assert_called_once_with(
            "https://hooks.slack.com/services/WEBHOOK",
            headers={"Content-Type": "application/json"},
            json=expected_payload,
        )

    def test_send_actual_alert(self):
        # Sending actual alert message to the chat
        self.slack_alerting.notify_alerts()
