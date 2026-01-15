from datetime import timedelta

from django.core import mail
from django.test import TestCase, override_settings
from django.utils import timezone
from impossible_travel.alerting.base_alerting import BaseAlerting
from impossible_travel.alerting.email_alerting import EmailAlerting
from impossible_travel.models import Alert, Login, User


class TestEmailAlerting(TestCase):
    @classmethod
    def setUpTestData(cls):
        """Set up test data once for all tests in this class."""
        cls.email_config = BaseAlerting.read_config("email")
        cls.email_alerting = EmailAlerting(cls.email_config)

        cls.user = User.objects.create(username="testuser")
        Login.objects.create(user=cls.user, id=cls.user.id)

        cls.alert = Alert.objects.create(
            name="Imp Travel",
            user=cls.user,
            notified_status={"email": False},
            description="Impossible travel detected",
            login_raw_data={},
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
        self.assertIn(f"Dear {self.user.username}", emailToUser.body)
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

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_clubbed_alerts(self):
        """Test that multiple similar alerts are clubbed into a single notification."""
        now = timezone.now()
        start_date = now - timedelta(minutes=30)
        end_date = now

        # Create two alerts within the 30min window
        alert1 = Alert.objects.create(
            name="Imp Travel",
            user=self.user,
            notified_status={"email": False},
            login_raw_data={},
        )
        alert2 = Alert.objects.create(
            name="Imp Travel",
            user=self.user,
            notified_status={"email": False},
            login_raw_data={},
        )
        alert3 = Alert.objects.create(
            name="New Country",
            user=self.user,
            notified_status={"email": False},
            login_raw_data={},
        )

        Alert.objects.filter(id=alert1.id).update(created=start_date + timedelta(minutes=10))
        Alert.objects.filter(id=alert2.id).update(created=start_date + timedelta(minutes=20))
        # This alert won't be notified as it's outside of the set range
        Alert.objects.filter(id=alert3.id).update(created=start_date - timedelta(hours=2))
        alert1.refresh_from_db()
        alert2.refresh_from_db()
        alert3.refresh_from_db()

        self.email_alerting.notify_alerts(start_date=start_date, end_date=end_date)

        # Verify that an email was sent
        self.assertEqual(len(mail.outbox), 1)

        # Verify email content
        emailToAdmin = mail.outbox[0]
        self.assertIn(
            'BuffaLogs - Login Anomaly Alerts : 3 "Imp Travel" alerts for user testuser',
            emailToAdmin.subject,
        )

        # Reload the alerts from the db
        alert1 = Alert.objects.get(pk=alert1.pk)
        alert2 = Alert.objects.get(pk=alert2.pk)
        alert2 = Alert.objects.get(pk=alert3.pk)

        self.assertTrue(alert1.notified_status["email"])
        self.assertFalse(alert2.notified_status["email"])
        self.assertFalse(alert3.notified_status["email"])
