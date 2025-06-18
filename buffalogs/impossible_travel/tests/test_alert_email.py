import json

from django.core import mail
from django.test import TestCase, override_settings
from impossible_travel.alerting.email_alerting import EmailAlerting
from impossible_travel.models import Alert, Login, User


class TestEmailAlerting(TestCase):

    def setUp(self):
        """Set up test data before running tests."""
        self.email_config = self._readConfig()
        self.email_alerting = EmailAlerting(self.email_config)

        # Create a dummy user
        self.user = User.objects.create(username="testuser")
        Login.objects.create(user=self.user, id=self.user.id)

        # Create an alert
        self.alert = Alert.objects.create(name="Imp Travel", user=self.user, notified=False, description="Impossible travel detected", login_raw_data={})

    def _readConfig(self):
        """Read the configuration file."""
        config_path = "../config/buffalogs/alerting.json"
        with open(config_path, mode="r", encoding="utf-8") as f:
            config = json.load(f)
        return config.get("email", {})

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_email_args(self):
        """Not sending the email actually,testing it in django's environment only"""
        self.email_alerting.notify_alerts()

        # Verify that an email was sent
        self.assertEqual(len(mail.outbox), 1)

        # Verify email content
        email = mail.outbox[0]

        self.assertEqual(email.subject, "Login Anomaly Alert: Imp Travel")
        self.assertEqual(email.body, "Dear user,\n\nAn unusual login activity has been detected:\n\nImpossible travel detected\n\nStay Safe,\nBuffalogs")
        self.assertEqual(email.from_email, "BuffaLogs Alerts SENDER_EMAIL")
        self.assertEqual(email.to, ["RECEIVER_EMAIL_ADDRESS", "RECEIVER_EMAIL_ADDRESS_2"])

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_no_alerts(self):
        """Test that no alerts are sent when there are no alerts to notify"""
        Alert.objects.all().update(notified=True)
        self.email_alerting.notify_alerts()
        self.assertEqual(len(mail.outbox), 0)

    def test_improper_config(self):
        """Test that an error is raised if the configuration is not correct"""
        with self.assertRaises(ValueError):
            EmailAlerting({})

    def test_send_email(self):
        """Actually sending the email to the recepient's address."""
        self.email_alerting.notify_alerts()
