from django.core import mail
from django.test import TestCase, override_settings
from impossible_travel.alerting.email_alerting import EmailAlerting
from impossible_travel.models import Alert, Login, User


class TestEmailAlerting(TestCase):

    def setUp(self):
        """Set up test data before running tests."""
        self.email_config = {
            "email_backend" : "django.core.mail.backends.locmem.EmailBackend",
            "email_server": "smtp.gmail.com",
            "email_port": 587,
            "email_use_tls": True,
            "email_host_user": "SENDER_EMAIL_ADDRESS",
            "email_host_password": "SENDER_APP_PASSWORD",
            "default_from_email": "BuffaLogs Alerts SENDER_EMAIL_ADRESS"
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
        self.assertEqual(email.from_email, "BuffaLogs Alerts SENDER_EMAIL_ADDRESS")
        self.assertEqual(email.to, ["RECIEVER_EMAIL_ADDRESS"])
    
    def test_send_email(self):
        """Actually sending the email to the recepient's address."""
        self.email_alerting.notify_alerts()

    
