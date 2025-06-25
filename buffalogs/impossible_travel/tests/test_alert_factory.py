from unittest.mock import patch

from django.test import TestCase
from impossible_travel.alerting.alert_factory import AlertFactory
from impossible_travel.alerting.base_alerting import BaseAlerting


class TestAlertFactory(TestCase):
    """Test the AlertFactory class."""

    def setUp(self):
        self.config = {
            "active_alerters": ["slack", "telegram"],
            "slack": {"webhook_url": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"},
            "telegram": {"bot_token": "BOT_TOKEN", "chat_ids": ["CHAT_ID"]},
            "discord": {"dummy": "value"},
        }

    def test_read_config(self):
        with patch.object(AlertFactory, "_read_config", return_value=self.config):
            alert_factory = AlertFactory()
            active_alerters = alert_factory.get_alert_classes()
            self.assertEqual(len(active_alerters), 2)
            self.assertIn("SlackAlerting", str(active_alerters[0]))
            self.assertIn("TelegramAlerting", str(active_alerters[1]))
