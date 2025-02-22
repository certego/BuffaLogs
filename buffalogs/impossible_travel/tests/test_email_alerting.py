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
            "email": {
                "host": "smtp.test.com",
                "port": 587,
                "sender": "test@buffalogs.com",
                "recipient": "test@example.com",
                "use_tls": True,
                "username": "testuser",
                "password": "testpass",
            }
        }

    @patch("smtplib.SMTP")
    def test_send_alert_email(self, mock_smtp):
        """Test successful email alert delivery"""
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

        mock_smtp.return_value.starttls.assert_called_once()
        mock_smtp.return_value.login.assert_called_with("testuser", "testpass")
        mock_smtp.return_value.send_message.assert_called_once()
        mock_smtp.return_value.quit.assert_called_once()

    def test_missing_config(self):
        """Test configuration validation"""
        with self.assertRaises(ValueError):
            EmailAlerting({"email": {"host": "bad"}})
