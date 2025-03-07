from unittest.mock import MagicMock, patch

from django.test import TestCase
from impossible_travel.alerting.pushover_alerting import PushoverAlerting
from impossible_travel.models import Alert, Login, User


class TestPushoverAlerting(TestCase):
    def setUp(self):
        """Set up test data before running tests."""

        self.pushover_config = {"api_key": "API_KEY", "user_key": "USER_TOKEN"}
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

        expected_payload = {
            "token": "API_KEY",
            "user": "USER_TOKEN",
            "message": "Login Anomaly Alert: Imp Travel\nDear user,\n\nAn unusual login activity has been detected:\n\nImpossible travel detected\n\nStay Safe,\nBuffalogs",
        }

        mock_post.assert_called_once_with("https://api.pushover.net/1/messages.json", data=expected_payload)

    """Use only one test at a time,usage of both test creates an error which maybe happens because
    You are running real alert sending (which changes database state) in the same test run as unit tests (which expect a fresh database).
    def test_send_actual_alert(self):
        #Sending actual alert message to the chat
        self.pushover_alerting.notify_alerts()
    """
