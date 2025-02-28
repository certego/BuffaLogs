from unittest import mock

from django.test import TestCase
from impossible_travel.alerting.http_alerting import HttpAlerting
from impossible_travel.models import Alert, User
from requests.exceptions import HTTPError


class TestHttpAlerting(TestCase):

    def setUp(self):
        "Setup user and alert"
        self.user = User.objects.create(username="test_user")
        self.alert = Alert.objects.create(
            user=self.user,
            name="New Country",
            description="This is a test alert",
            notified=False,
            login_raw_data={},
        )
        self.http_config = HttpAlerting(
            alert_config={
                "endpoint_url": "https://api.example.com/alerts",
                "headers": {
                    "Authorization": "Bearer YOUR_TOKEN",
                    "Content-Type": "application/json",
                },
                "timeout": 10,
            }
        )

    @mock.patch("requests.post")
    def test_notify_alerts_success(self, mock_post):
        """Test send alerts and mark them as notified."""
        # Configure mock response
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        # Execute the notification
        self.http_config.notify_alerts()

        # Refresh the alert from the database
        self.alert.refresh_from_db()

        # POST request was made with correct data
        expected_data = {
            "user": self.user.username,
            "alert_name": self.alert.name,
            "description": self.alert.description,
            "created": self.alert.created,
        }
        mock_post.assert_called_once_with(
            "https://api.example.com/alerts",
            json=expected_data,
            headers={
                "Authorization": "Bearer YOUR_TOKEN",
                "Content-Type": "application/json",
            },
            timeout=10,
        )
        # Verify the alert is marked as notified
        self.assertTrue(self.alert.notified)

    @mock.patch("requests.post")
    def test_notify_alerts_http_error(self, mock_post):
        """Test handles a HTTP errors during alert notification."""
        # Configure mock to raise an HTTP error
        mock_response = mock.Mock()
        mock_response.raise_for_status.side_effect = HTTPError("HTTP Error")
        mock_post.return_value = mock_response

        # Execute the notification
        self.http_config.notify_alerts()

        # Refresh the alert from the database
        self.alert.refresh_from_db()

        # Verify the alert is not marked as notified
        self.assertFalse(self.alert.notified)

    def test_send_actual_alert(self):
        """Sending real alert message"""
        self.http_config.notify_alerts()
