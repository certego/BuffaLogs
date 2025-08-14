from datetime import timedelta
from unittest.mock import MagicMock, patch

import requests
from django.test import TestCase
from django.utils import timezone
from impossible_travel.alerting.base_alerting import BaseAlerting
from impossible_travel.alerting.slack_alerting import SlackAlerting
from impossible_travel.models import Alert, Login, User


class TestSlackAlerting(TestCase):
    @classmethod
    def setUpTestData(cls):
        """Set up test data once for all tests in this class."""
        cls.slack_config = BaseAlerting.read_config("slack")
        cls.slack_alerting = SlackAlerting(cls.slack_config)

        # Create shared test user and login
        cls.user = User.objects.create(username="testuser")
        Login.objects.create(user=cls.user, id=cls.user.id)

        # Create alert
        cls.alert = Alert.objects.create(
            name="Imp Travel", user=cls.user, notified_status={"slack": False}, description="Impossible travel detected", login_raw_data={}
        )

    @patch("requests.post")
    def test_send_alert(self, mock_post):
        """Doesn't actually sends the Alert,a mock request is sent"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        self.slack_alerting.notify_alerts()

        expected_alert_title, expected_alert_description = BaseAlerting.alert_message_formatter(self.alert)
        expected_payload = {
            "attachments": [
                {
                    "title": expected_alert_title,
                    "text": expected_alert_description,
                    "color": "#ff0000",
                }
            ]
        }

        mock_post.assert_called_once_with(
            self.slack_config["webhook_url"],
            headers={"Content-Type": "application/json"},
            json=expected_payload,
        )

    @patch("requests.post")
    def test_no_alerts(self, mock_post):
        """Test that no alerts are sent when there are no alerts to notify"""
        for alert in Alert.objects.all():
            alert.notified_status["slack"] = True
            alert.save()
        self.slack_alerting.notify_alerts()
        self.assertEqual(mock_post.call_count, 0)

    def test_improper_config(self):
        """Test that an error is raised if the configuration is not correct"""
        with self.assertRaises(ValueError):
            SlackAlerting({})

    @patch("requests.post")
    def test_alert_network_failure(self, mock_post):
        """Test that alert is not marked as notified if there are any Network Fails"""
        # Simulate network/API failure
        mock_post.side_effect = requests.RequestException()

        self.slack_alerting.notify_alerts()

        # Reload the alert from DB to check its state
        alert = Alert.objects.get(pk=self.alert.pk)
        self.assertFalse(alert.notified_status["slack"])

    @patch("requests.post")
    def test_clubbed_alerts(self, mock_post):
        """Test that multiple similar alerts are clubbed into a single notification."""
        now = timezone.now()

        # Create two alerts within the 30min window
        alert1 = Alert.objects.create(
            name="Imp Travel",
            user=self.user,
            notified_status={"slack": False},
            description="Impossible travel detected - Attempt 1",
            created=now - timedelta(minutes=10),
            login_raw_data={},
        )
        alert2 = Alert.objects.create(
            name="Imp Travel",
            user=self.user,
            notified_status={"slack": False},
            description="Impossible travel detected - Attempt 2",
            created=now - timedelta(minutes=5),
            login_raw_data={},
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        start_date = now - timedelta(minutes=30)
        end_date = now
        self.slack_alerting.notify_alerts(start_date=start_date, end_date=end_date)
        # Assert that only one Slack notification was sent
        self.assertEqual(mock_post.call_count, 1)
