import json
from unittest.mock import MagicMock, patch

from django.test import TestCase
from impossible_travel.alerting.microsoft_teams_alerting import MicrosoftTeamsAlerting
from impossible_travel.models import Alert, Login, User


class TestMicrosoftTeamsAlerting(TestCase):
    def setUp(self):
        """Set up test data before running tests."""

        self.teams_config = {"webhook_url": "https://example.com/webhook/id/webhook/unique-id/token"}
        self.teams_alerting = MicrosoftTeamsAlerting(self.teams_config)

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

        self.teams_alerting.notify_alerts()

        expected_payload = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": "FF0000",
            "title": "Login Anomaly Alert: Imp Travel",
            "text": "Dear user,\n\nAn unusual login activity has been detected:\n\nImpossible travel detected\n\nStay Safe,\nBuffalogs",
        }

        mock_post.assert_called_once_with(
            "https://example.com/webhook/id/webhook/unique-id/token",
            headers={"Content-Type": "application/json"},
            data=json.dumps(expected_payload),
        )

    def test_send_actual_alert(self):
        # Sending actual alert message to the chat
        self.teams_alerting.notify_alerts()
