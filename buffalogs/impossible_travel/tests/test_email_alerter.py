import unittest
import sys
import os

# Add the root directory of the project to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

from buffalogs.impossible_travel.alerting.email_alerter import EmailAlerter
from unittest.mock import patch, MagicMock

class TestEmailAlerter(unittest.TestCase):
    @patch('smtplib.SMTP')
    def test_send_alert(self, mock_smtp):
        smtp_instance = mock_smtp.return_value
        smtp_instance.sendmail = MagicMock()

        alerter = EmailAlerter(
            smtp_server="smtp.example.com",
            smtp_port=587,
            username="your_username",
            password="your_password",
            from_addr="from@example.com",
            to_addrs=["to1@example.com", "to2@example.com"]
        )

        alerter.send_alert("Test Subject", "Test Message")

        smtp_instance.sendmail.assert_called_once()

if __name__ == '__main__':
    unittest.main()