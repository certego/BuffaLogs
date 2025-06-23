import json
from unittest.mock import MagicMock, patch

import requests
from django.test import TestCase
from impossible_travel.alerting.base_alerting import BaseAlerting
from impossible_travel.alerting.pushover_alerting import PushoverAlerting
from impossible_travel.models import Alert, Login, User


class TestPushoverAlerting(TestCase):
    def setUp(self):
        """Set up test data before running tests."""

        self.pushover_config = BaseAlerting.read_config("pushover")
        self.pushover_alerting = PushoverAlerting(self.pushover_config)

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

        self.pushover_alerting.notify_alerts()

        expected_alert_title, expected_alert_description = BaseAlerting.alert_message_formatter(self.alert)
        expected_alert_msg = expected_alert_title + "\n\n" + expected_alert_description
        expected_payload = {"token": self.pushover_config["api_key"], "user": self.pushover_config["user_key"], "message": expected_alert_msg}

        mock_post.assert_called_once_with("https://api.pushover.net/1/messages.json", data=expected_payload)

    @patch("requests.post")
    def test_no_alerts(self, mock_post):
        """Test that no alerts are sent when there are no alerts to notify"""
        Alert.objects.all().update(notified=True)
        self.pushover_alerting.notify_alerts()
        self.assertEqual(mock_post.call_count, 0)

    def test_improper_config(self):
        """Test that an error is raised if the configuration is not correct"""
        with self.assertRaises(ValueError):
            PushoverAlerting({})

    @patch("requests.post")
    def test_alert_network_failure(self, mock_post):
        """Test that alert is not marked as notified if there are any Network Fails"""
        # Simulate network/API failure
        mock_post.side_effect = requests.RequestException()

        self.pushover_alerting.notify_alerts()

        # Reload the alert from DB to check its state
        alert = Alert.objects.get(pk=self.alert.pk)
        self.assertFalse(alert.notified)

    def test_send_actual_alert(self):
        """Test sending an actual alert"""
        self.pushover_alerting.notify_alerts()
