from django.conf import settings
from django.test import TestCase
from django.core import mail
from django.test import override_settings
from impossible_travel.modules import alert_email

class TestAlertEmail(TestCase):
    #uncomment this to actually send the test mail
    #@override_settings(EMAIL_BACKEND="django.core.mail.backends.smtp.EmailBackend")
    def test_send_email(self):
        #sends an email
        alert_email.send_alert_email('SEND_ALERT_TO_THIS_ADDRESS','testing4')
        
        # Check if one email was sent
        self.assertEqual(len(mail.outbox), 1)

        # Verify email subject
        self.assertEqual(mail.outbox[0].subject, "Login Anomaly Detected")

        # Verify email recipient
        self.assertEqual(mail.outbox[0].to, ["SEND_ALERT_TO_THIS_ADDRESS"])


