from django.core import mail
from django.test import TestCase, override_settings
from impossible_travel.alerting.base_alerting import BaseAlerting
from impossible_travel.alerting.email_alerting import EmailAlerting
from impossible_travel.models import Alert, Login, User


class TestEmailAlerting(TestCase):

    def setUp(self):
        """Set up test data before running tests."""
        self.email_config = BaseAlerting.read_config("email")
        self.email_alerting = EmailAlerting(self.email_config)

        # Create a dummy user
        self.user = User.objects.create(username="testuser")
        Login.objects.create(user=self.user, id=self.user.id)

        # Create an alert
        self.alert = Alert.objects.create(
            name="Imp Travel", user=self.user, notified_status={"email": False}, description="Impossible travel detected", login_raw_data={}
        )

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_email_args(self):
        """Not sending the email actually,testing it in django's environment only"""
        self.email_alerting.notify_alerts()

        # Verify that an email was sent
        self.assertEqual(len(mail.outbox), 2)

        # Verify email content
        emailToAdmin = mail.outbox[0]
        emailToUser = mail.outbox[1]

        expected_alert_title, expected_alert_description = BaseAlerting.alert_message_formatter(self.alert)
        expected_from_email = self.email_config.get("default_from_email")
        expected_recipient_list_admins = self.email_config.get("recipient_list_admins")
        expected_recipient_list_users = self.email_config.get("recipient_list_users")

        # Checks for email sent to admin
        self.assertEqual(emailToAdmin.subject, expected_alert_title)
        self.assertEqual(emailToAdmin.body, expected_alert_description)
        self.assertEqual(emailToAdmin.from_email, expected_from_email)
        self.assertEqual(emailToAdmin.to, expected_recipient_list_admins)

        # Checks for email sent to user
        self.assertEqual(emailToUser.subject, "BuffaLogs - Login Anomaly Alert: Imp Travel")
        self.assertIn("Dear testuser", emailToUser.body)
        self.assertEqual(emailToUser.from_email, expected_from_email)
        self.assertEqual(emailToUser.to, [expected_recipient_list_users[self.user.username]])

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_no_alerts(self):
        """Test that no alerts are sent when there are no alerts to notify"""
        for alert in Alert.objects.all():
            alert.notified_status["email"] = True
            alert.save()
        self.email_alerting.notify_alerts()
        self.assertEqual(len(mail.outbox), 0)

    def test_improper_config(self):
        """Test that an error is raised if the configuration is not correct"""
        with self.assertRaises(ValueError):
            EmailAlerting({})
