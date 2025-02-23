from django.test import TestCase
from impossible_travel.alerting.email_alerting import EmailAlerting
from impossible_travel.models import Alert, User
from unittest.mock import patch


class TestEmailAlerting(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username="testuser")

    def setUp(self):
        self.alert_config = {
            "host": "smtp.test.com",
            "port": 587,
            "sender": "test@buffalogs.com",
            "recipient": "test@example.com",
            "use_tls": True,
            "username": "testuser",
            "password": "testpass",
        }

    @patch("smtplib.SMTP")
    def test_send_alert_email(self, mock_smtp):
        alert = Alert.objects.create(
            name="Imp Travel",
            user=self.user,
            login_raw_data={"risk_score": 85},
            description="Impossible travel detected",
        )

        alerter = EmailAlerting(self.alert_config)
        alerter.notify_alerts() 

        alert.refresh_from_db()
        self.assertTrue(alert.notified)

    def test_missing_config(self):
        """Test with missing required fields"""
        with self.assertRaises(ValueError):
            EmailAlerting({"host": "bad"})
