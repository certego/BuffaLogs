from unittest.mock import MagicMock, patch

from django.test import TestCase

from impossible_travel.alerting.alert_factory import AlertFactory
from impossible_travel.alerting.base_alerting import BaseAlerting
from impossible_travel.models import Alert, Login, User


class TestAlertFactory(TestCase):
    """Test the AlertFactory class."""

    def setUp(self):
        self.config = {
            "active_alerters": ["slack", "telegram"],
            "telegram": {"bot_token": "BOT_TOKEN", "chat_ids": ["CHAT_ID"]},
            "slack": {"webhook_url": "WEBHOOK_URL"},
            "discord": {"dummy": "dummy"},
        }

        # Create a dummy user
        self.user = User.objects.create(username="testuser")
        Login.objects.create(user=self.user, id=self.user.id)

        # Create an alert
        self.alert = Alert.objects.create(
            name="Imp Travel",
            user=self.user,
            notified_status={
                "telegram": False,
                "slack": False,
                "discord": False,
            },
            description="Impossible travel detected",
            login_raw_data={},
        )

    def test_read_config(self):
        with patch.object(
            AlertFactory, "_read_config", return_value=self.config
        ):
            alert_factory = AlertFactory()
            active_alerters = alert_factory.get_alert_classes()
            self.assertEqual(len(active_alerters), 2)
            self.assertIn("SlackAlerting", str(active_alerters[0]))
            self.assertIn("TelegramAlerting", str(active_alerters[1]))

    def test_send_actual_alert(self):
        with patch.object(
            AlertFactory, "_read_config", return_value=self.config
        ):
            alert_factory = AlertFactory()
            active_alerters = alert_factory.get_alert_classes()
            for alerter in active_alerters:
                # This will again set the notified status to True
                alerter.notify_alerts()

    @patch("requests.post")
    def test_send_mock_alert(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        with patch.object(
            AlertFactory, "_read_config", return_value=self.config
        ):
            alert_factory = AlertFactory()
            active_alerters = alert_factory.get_alert_classes()
            for alerter in active_alerters:
                alerter.notify_alerts()

                expected_alert_title, expected_alert_description = (
                    BaseAlerting.alert_message_formatter(self.alert)
                )
                expected_alert_msg = (
                    expected_alert_title + "\n\n" + expected_alert_description
                )

                if alerter.__class__.__name__ == "SlackAlerting":
                    expected_payload = {
                        "attachments": [
                            {
                                "title": expected_alert_title,
                                "text": expected_alert_description,
                                "color": "#ff0000",
                            }
                        ]
                    }

                    mock_post.assert_any_call(
                        self.config["slack"]["webhook_url"],
                        headers={"Content-Type": "application/json"},
                        json=expected_payload,
                    )

                elif alerter.__class__.__name__ == "TelegramAlerting":
                    expected_payload = {
                        "chat_id": f"{self.config['telegram']['chat_ids'][0]}",
                        "text": expected_alert_msg,
                    }

                    mock_post.assert_any_call(
                        f"https://api.telegram.org/bot{self.config['telegram']['bot_token']}/sendMessage",
                        json=expected_payload,
                    )
