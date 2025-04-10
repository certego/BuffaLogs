import json
from unittest.mock import MagicMock, patch

import requests
from django.test import TestCase
from impossible_travel.alerting.microsoft_teams_alerter import MicrosoftTeamsAlerting
from impossible_travel.models import Alert, User


class TestTeamAlerting(TestCase):
    def setUp(self):
        self.teams_config = {"webhook_url": "https://example.com/webhook/id/webhook/unique-id/token"}
        self.teams_alerting = MicrosoftTeamsAlerting(self.teams_config)

        # Creating test user and alert
        self.user = User.objects.create(username="testuser")
        self.alert = Alert.objects.create(name="Imp Travel", user=self.user, notified=False, description="Impossible travel detected", login_raw_data={})

        self.expected_payload = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": "FF0000",
            "title": "Security Alert: Imp Travel",
            "text": "Impossible travel detected\n\nstay safe, BuffaLogs",
        }

    @patch("requests.post")
    def test_successful_notification(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        self.teams_alerting.notify_alerts()

        # Verifying database update
        updated_alert = Alert.objects.get(id=self.alert.id)
        self.assertTrue(updated_alert.notified)

        mock_post.assert_called_once_with(
            self.teams_config.get("webhook_url"), headers={"Content-Type": "application/json"}, data=json.dumps(self.expected_payload)
        )

    @patch("requests.post")
    def test_failed_notification(self, mock_post):
        mock_post.side_effect = requests.exceptions.RequestException("Connection Error")

        self.teams_alerting.notify_alerts()

        updated_alert = Alert.objects.get(id=self.alert.id)
        self.assertFalse(updated_alert.notified)

        mock_post.assert_called_once_with(
            self.teams_config.get("webhook_url"), headers={"Content-Type": "application/json"}, data=json.dumps(self.expected_payload)
        )
