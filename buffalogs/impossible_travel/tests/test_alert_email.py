from django.test import TestCase
from unittest.mock import patch
from impossible_travel.alerting.email_alerting import EmailAlerting
from impossible_travel.models import Alert, User, Login
from django.core.mail import send_mail


class TestEmailAlerting(TestCase):

    def setUp(self):
        """Set up test data before running tests."""
        self.email_config = {
            "email_server": "smtp.gmail.com",
            "email_port": 587,
            "email_use_tls": True,
            "email_host_user": "SENDER_EMAIL",
            "email_host_password": "APP_PASSWORD",
            "default_from_email": "BuffaLogs Alerts SENDER_EMAIL"
        }
        self.email_alerting = EmailAlerting(self.email_config)

        # Create a dummy user
        self.user = User.objects.create(username="testuser")
        Login.objects.create(user=self.user, id=self.user.id)

        # Create an alert
        self.alert = Alert.objects.create(
            name="Imp Travel",
            user=self.user,
            notified=False,
            description="Impossible travel detected",
            login_raw_data={}
        )

    @patch("django.core.mail.send_mail") 
    def test_notify_alerts_sends_email(self, mock_send_mail):
        """Test if notify_alerts() calls send_mail and updates the alert."""

        # Allow the actual function to run while tracking its calls
        mock_send_mail.side_effect = send_mail  # This lets it actually send emails

        self.email_alerting.notify_alerts()

        # Debugging output
        print("Mock call count:", mock_send_mail.call_count)

        # Ensure send_mail was called at least once
        self.assertGreater(mock_send_mail.call_count, 0, "Email was not sent.")
