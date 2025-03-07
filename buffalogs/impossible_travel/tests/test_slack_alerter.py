from unittest import TestCase
from unittest.mock import MagicMock, patch

from ..alerting.slack_alerter import SlackAlerter


class TestSlackAlerter(TestCase):
    def setUp(self):
        self.slack_config = {"webhook_url": "https://hooks.slack.com/services/TEST/TEST/TEST", "channel": "#test-channel"}
        self.alert_data = {"user": "test_user", "timestamp": "2025-02-28T12:00:00Z", "location1": "New York", "location2": "Tokyo"}

    def test_slack_alerter_initialization(self):
        alerter = SlackAlerter(self.slack_config)
        self.assertEqual(alerter.webhook_url, self.slack_config["webhook_url"])
        self.assertEqual(alerter.channel, self.slack_config["channel"])

    def test_slack_alerter_missing_webhook(self):
        with self.assertRaises(ValueError):
            SlackAlerter({})

    @patch("requests.post")
    def test_send_alert_success(self, mock_post):
        mock_post.return_value = MagicMock(status_code=200)
        alerter = SlackAlerter(self.slack_config)
        self.assertTrue(alerter.send_alert(self.alert_data))
        mock_post.assert_called_once()

    @patch("requests.post")
    def test_send_alert_failure(self, mock_post):
        mock_post.side_effect = Exception("Connection error")
        alerter = SlackAlerter(self.slack_config)
        self.assertFalse(alerter.send_alert(self.alert_data))
        self.assertFalse(alerter.send_alert(self.alert_data))
