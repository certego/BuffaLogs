from unittest.mock import MagicMock, patch

import requests
from django.test import TestCase
from impossible_travel.alerting.base_alerting import BaseAlerting
from impossible_travel.alerting.googlechat_alerting import GoogleChatAlerting
from impossible_travel.models import Alert, Login, User


class TestGoogleChatAlerting(TestCase):
    @classmethod
    def setUpTestData(cls):
        """Set up test data once for all tests in this class."""
        cls.googlechat_config = BaseAlerting.read_config("googlechat")
        cls.googlechat_alerting = GoogleChatAlerting(cls.googlechat_config)

        # Shared user and login
        cls.user = User.objects.create(username="testuser")
        Login.objects.create(user=cls.user, id=cls.user.id)

        # Shared alert
        cls.alert = Alert.objects.create(
            name="Imp Travel", user=cls.user, notified_status={"googlechat": False}, description="Impossible travel detected", login_raw_data={}
        )

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
        for alert in Alert.objects.all():
            alert.notified_status["googlechat"] = True
            alert.save()
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
        self.assertFalse(alert.notified_status["googlechat"])
