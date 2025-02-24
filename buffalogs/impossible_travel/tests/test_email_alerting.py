from django.test import TestCase
from unittest.mock import patch
from django.core import mail
from impossible_travel.alerting.email_alerting import EmailAlerting
from impossible_travel.models import Alert, User, Login


class TestEmailAlerting(TestCase):

    def setUp(self):
        # Valid email configuration
        self.valid_config = {
            "email_server": "smtp.gmail.com",
            "email_port": 587,
            "email_use_tls": True,
            "email_host_user": "user@example.com",
            "email_host_password": "password",
            "default_from_email": "alerts@example.com",
            "recipient_list": ["admin@example.com"],
        }

        # Create test user and alert
        self.user = User.objects.create(username="testuser")
        Login.objects.create(user=self.user, id=self.user.id)
        self.alert = Alert.objects.create(
            name="New Country",
            user=self.user,
            description="Test alert description",
            notified=False,
            login_raw_data={},
        )

    def test_valid_configuration(self):
        """Test initialization with valid configuration"""
        alerter = EmailAlerting(self.valid_config)
        self.assertIsInstance(alerter, EmailAlerting)

    def test_invalid_configuration(self):
        """Test initialization with missing required parameters"""
        invalid_config = self.valid_config.copy()
        del invalid_config["email_host_password"]

        with self.assertRaises(ValueError) as context:
            EmailAlerting(invalid_config)

        self.assertIn("Missing email configuration keys", str(context.exception))

    @patch.object(EmailAlerting, "send_email")
    def test_notify_alerts_updates_status(self, mock_send_email):
        """Test that alerts are marked as notified after processing"""
        alerter = EmailAlerting(self.valid_config)
        alerter.notify_alerts()

        self.alert.refresh_from_db()
        self.assertTrue(self.alert.notified)
        mock_send_email.assert_called_once_with(self.alert)

    @patch("django.core.mail.send_mail")
    def test_email_sending_success(self, mock_send):
        """Test successful email sending with correct parameters"""
        alerter = EmailAlerting(self.valid_config)
        alerter.notify_alerts()

        # Verify email parameters
        mock_send.assert_called_once()
        args, kwargs = mock_send.call_args
        self.assertEqual(args[0], "Alert: New Country")
        self.assertIn("Test alert description", args[1])
        self.assertEqual(args[2], "alerts@example.com")
        self.assertEqual(args[3], ["admin@example.com"])

    def test_email_sending_no_recipients(self):
        """Test email skips sending when no recipients configured"""
        no_recipient_config = self.valid_config.copy()
        no_recipient_config["recipient_list"] = []

        with patch("django.core.mail.send_mail") as mock_send:
            alerter = EmailAlerting(no_recipient_config)
            alerter.notify_alerts()

            mock_send.assert_not_called()
            self.alert.refresh_from_db()
            self.assertTrue(self.alert.notified)  # Should still mark as notified
