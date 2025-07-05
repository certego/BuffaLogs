from unittest.mock import MagicMock, patch

import requests
from django.test import TestCase
from impossible_travel.alerting.base_alerting import BaseAlerting
from impossible_travel.alerting.googlechat_alerting import GoogleChatAlerting
from impossible_travel.models import Alert, Login, User


class TestGoogleChatAlerting(TestCase):
    def setUp(self):
        """Set up test data before running tests."""

        self.googlechat_config = BaseAlerting.read_config("googlechat")
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

        expected_alert_title, expected_alert_description = BaseAlerting.alert_message_formatter(self.alert)

        expected_payload = {
            "cards": [
                {
                    "header": {"title": expected_alert_title},
                    "sections": [{"widgets": [{"textParagraph": {"text": expected_alert_description}}]}],
                }
            ]
        }

        mock_post.assert_called_once_with(
            self.googlechat_config["webhook_url"],
            json=expected_payload,
        )

    @patch("requests.post")
    def test_no_alerts(self, mock_post):
        """Test that no alerts are sent when there are no alerts to notify"""
        Alert.objects.all().update(notified=True)
        self.googlechat_alerting.notify_alerts()
        self.assertEqual(mock_post.call_count, 0)

    def test_improper_config(self):
        """Test that an error is raised if the configuration is not correct"""
        with self.assertRaises(ValueError):
            GoogleChatAlerting({})

    @patch("requests.post")
    def test_alert_network_failure(self, mock_post):
        """Test that alert is not marked as notified if there are any Network Fails"""
        # Simulate network/API failure
        mock_post.side_effect = requests.RequestException()

        self.googlechat_alerting.notify_alerts()

        # Reload the alert from DB to check its state
        alert = Alert.objects.get(pk=self.alert.pk)
        self.assertFalse(alert.notified)

    def test_send_actual_alert(self):
        """Test sending an actual alert"""
        self.googlechat_alerting.notify_alerts()
