import json
from datetime import timedelta
from unittest.mock import MagicMock, patch

import requests
from django.test import TestCase
from django.utils import timezone
from impossible_travel.alerting.base_alerting import BaseAlerting
from impossible_travel.alerting.microsoft_teams_alerting import MicrosoftTeamsAlerting
from impossible_travel.models import Alert, Login, User


class TestMicrosoftTeamsAlerting(TestCase):
    @classmethod
    def setUpTestData(cls):
        """Set up test data once for all tests in this class."""
        cls.teams_config = BaseAlerting.read_config("microsoftteams")
        cls.teams_alerting = MicrosoftTeamsAlerting(cls.teams_config)

        # Create shared user and login
        cls.user = User.objects.create(username="testuser")
        Login.objects.create(user=cls.user, id=cls.user.id)

        # Create shared alert
        cls.alert = Alert.objects.create(
            name="Imp Travel", user=cls.user, notified_status={"microsoftteams": False}, description="Impossible travel detected", login_raw_data={}
        )

    @patch("requests.post")
    def test_send_alert(self, mock_post):
        """Doesn't actually sends the Alert,a mock request is sent"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        self.teams_alerting.notify_alerts()

        expected_alert_title, expected_alert_description = BaseAlerting.alert_message_formatter(self.alert)

        expected_payload = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": "FF0000",
            "title": expected_alert_title,
            "text": expected_alert_description,
        }

        mock_post.assert_called_once_with(
            self.teams_config["webhook_url"],
            headers={"Content-Type": "application/json"},
            data=json.dumps(expected_payload),
        )

    @patch("requests.post")
    def test_no_alerts(self, mock_post):
        """Test that no alerts are sent when there are no alerts to notify"""
        for alert in Alert.objects.all():
            alert.notified_status["microsoftteams"] = True
            alert.save()
        self.teams_alerting.notify_alerts()
        self.assertEqual(mock_post.call_count, 0)

    def test_improper_config(self):
        """Test that an error is raised if the configuration is not correct"""
        with self.assertRaises(ValueError):
            MicrosoftTeamsAlerting({})

    @patch("requests.post")
    def test_alert_network_failure(self, mock_post):
        """Test that alert is not marked as notified if there are any Network Fails"""
        # Simulate network/API failure
        mock_post.side_effect = requests.RequestException()

        self.teams_alerting.notify_alerts()

        # Reload the alert from DB to check its state
        alert = Alert.objects.get(pk=self.alert.pk)
        self.assertFalse(alert.notified_status["microsoftteams"])

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
            notified_status={"microsoftteams": False},
            login_raw_data={},
        )
        alert2 = Alert.objects.create(
            name="Imp Travel",
            user=self.user,
            notified_status={"microsoftteams": False},
            login_raw_data={},
        )
        alert3 = Alert.objects.create(
            name="New Country",
            user=self.user,
            notified_status={"microsoftteams": False},
            login_raw_data={},
        )

        Alert.objects.filter(id=alert1.id).update(created=start_date + timedelta(minutes=10))
        Alert.objects.filter(id=alert2.id).update(created=start_date + timedelta(minutes=20))
        # This alert won't be notified as it's outside of the set range
        Alert.objects.filter(id=alert3.id).update(created=start_date - timedelta(hours=2))
        alert1.refresh_from_db()
        alert2.refresh_from_db()
        alert3.refresh_from_db()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        self.teams_alerting.notify_alerts(start_date=start_date, end_date=end_date)

        args, kwargs = mock_post.call_args
        title = kwargs["data"]

        # 3 Imp Travel Alerts will be clubbed
        self.assertIn("BuffaLogs - Login Anomaly Alerts : 3", title)
        # Reload the alerts from the db
        alert1 = Alert.objects.get(pk=alert1.pk)
        alert2 = Alert.objects.get(pk=alert2.pk)
        alert2 = Alert.objects.get(pk=alert3.pk)

        self.assertTrue(alert1.notified_status["microsoftteams"])
        self.assertFalse(alert2.notified_status["microsoftteams"])
        self.assertFalse(alert3.notified_status["microsoftteams"])
