from datetime import timedelta
from unittest.mock import MagicMock, patch

from django.test import TestCase
from django.utils import timezone
from impossible_travel.alerting.base_alerting import BaseAlerting
from impossible_travel.alerting.pushover_alerting import PushoverAlerting
from impossible_travel.models import Alert, Login, User
import requests


class TestPushoverAlerting(TestCase):
    @classmethod
    def setUpTestData(cls):
        """Set up test data once for all tests in this class."""
        cls.pushover_config = BaseAlerting.read_config("pushover")
        cls.pushover_alerting = PushoverAlerting(cls.pushover_config)

        # Create shared user and login
        cls.user = User.objects.create(username="testuser")
        Login.objects.create(user=cls.user, id=cls.user.id)

        # Create shared alert
        cls.alert = Alert.objects.create(
            name="Imp Travel",
            user=cls.user,
            notified_status={"pushover": False},
            description="Impossible travel detected",
            login_raw_data={},
        )

    @patch("requests.post")
    def test_send_alert(self, mock_post):
        """Doesn't actually sends the Alert,a mock request is sent"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        self.pushover_alerting.notify_alerts()

        (
            expected_alert_title,
            expected_alert_description,
        ) = BaseAlerting.alert_message_formatter(self.alert)
        expected_alert_msg = expected_alert_title + "\n\n" + expected_alert_description
        expected_payload = {
            "token": self.pushover_config["api_key"],
            "user": self.pushover_config["user_key"],
            "message": expected_alert_msg,
        }

        mock_post.assert_called_once_with(
            "https://api.pushover.net/1/messages.json", data=expected_payload
        )

    @patch("requests.post")
    def test_no_alerts(self, mock_post):
        """Test that no alerts are sent when there are no alerts to notify"""
        for alert in Alert.objects.all():
            alert.notified_status["pushover"] = True
            alert.save()
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
        self.assertFalse(alert.notified_status["pushover"])

    @patch("requests.post")
    def test_clubbed_alerts(self, mock_post):
        """Test that multiple similar alerts are clubbed into a single notification."""
        now = timezone.now()
        start_date = now - timedelta(minutes=30)
        end_date = now

        # Create two alerts within the 30min window
        alert1 = Alert.objects.create(
            name="Imp Travel",
            user=self.user,
            notified_status={"pushover": False},
            login_raw_data={},
        )
        alert2 = Alert.objects.create(
            name="Imp Travel",
            user=self.user,
            notified_status={"pushover": False},
            login_raw_data={},
        )
        alert3 = Alert.objects.create(
            name="New Country",
            user=self.user,
            notified_status={"pushover": False},
            login_raw_data={},
        )

        Alert.objects.filter(id=alert1.id).update(
            created=start_date + timedelta(minutes=10)
        )
        Alert.objects.filter(id=alert2.id).update(
            created=start_date + timedelta(minutes=20)
        )
        # This alert won't be notified as it's outside of the set range
        Alert.objects.filter(id=alert3.id).update(
            created=start_date - timedelta(hours=2)
        )
        alert1.refresh_from_db()
        alert2.refresh_from_db()
        alert3.refresh_from_db()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        self.pushover_alerting.notify_alerts(start_date=start_date, end_date=end_date)

        args, kwargs = mock_post.call_args
        message = kwargs["data"]["message"]

        # 3 Imp Travel Alerts will be clubbed
        self.assertIn(
            'BuffaLogs - Login Anomaly Alerts : 3 "Imp Travel" alerts for user testuser',
            message,
        )
        # Reload the alerts from the db
        alert1 = Alert.objects.get(pk=alert1.pk)
        alert2 = Alert.objects.get(pk=alert2.pk)
        alert2 = Alert.objects.get(pk=alert3.pk)

        self.assertTrue(alert1.notified_status["pushover"])
        self.assertFalse(alert2.notified_status["pushover"])
        self.assertFalse(alert3.notified_status["pushover"])
