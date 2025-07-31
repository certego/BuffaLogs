import json
from unittest import mock

from django.test import Client
from django.urls import reverse
from rest_framework.test import APITestCase


def mock_read_config(filename: str, key: str | None = None):
    config = {
        "active_alerters": ["discord"],
        "slack": {"webhook_url": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"},
        "telegram": {"bot_token": "BOT_TOKEN", "chat_ids": ["CHAT_ID"]},
        "dummy": {"config_field_example": "value_example"},
        "email": {
            "email_backend": "django.core.mail.backends.smtp.EmailBackend",
            "email_server": "smtp.gmail.com",
            "email_port": 587,
            "email_use_tls": "True",
            "email_host_user": "SENDER_EMAIL",
            "email_host_password": "SENDER_APP_PASSWORD",
            "default_from_email": "BuffaLogs Alerts SENDER_EMAIL",
            "recipient_list_admins": ["RECEIVER_EMAIL_ADDRESS", "RECEIVER_EMAIL_ADDRESS_2"],
            "recipient_list_users": {"testuser": "testuser@test.com"},
        },
        "http_request": {
            "name": "",
            "endpoint": "",
            "options": {"token_variable_name": "", "alert_types": [], "fields": [], "login_data": [], "batch_size": -1},
        },
        "discord": {"webhook_url": "https://discord.com/api/webhooks/WEBHOOK", "username": "BuffaLogs_Alert"},
    }
    if key:
        return config[key]
    return config


def mock_write_config(filename: str, key: str, updates: dict[str, str]):
    pass


class TestAlertAPI(APITestCase):
    def setUp(self):
        self.client = Client()

    def test_get_alert_types(self):
        expected = [
            {"alert_type": "New Device", "description": "Login from new device"},
            {"alert_type": "Imp Travel", "description": "Impossible Travel detected"},
            {"alert_type": "New Country", "description": "Login from new country"},
            {"alert_type": "User Risk Threshold", "description": "User risk_score increased"},
            {"alert_type": "Anonymous IP Login", "description": "Login from an anonymous IP"},
            {"alert_type": "Atypical Country", "description": "Login from an atypical country"},
        ]

        response = self.client.get(reverse("alert_types"))
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        self.assertEqual(content, expected)

    @mock.patch("impossible_travel.views.alerts.read_config", side_effect=mock_read_config)
    def test_get_alerters(self, mock_reader):
        expected = [
            {"alerter": "slack", "fields": ["webhook_url"], "options": []},
            {"alerter": "telegram", "fields": ["bot_token", "chat_ids"], "options": []},
            {
                "alerter": "email",
                "fields": [
                    "email_backend",
                    "email_server",
                    "email_port",
                    "email_use_tls",
                    "email_host_user",
                    "email_host_password",
                    "default_from_email",
                    "recipient_list_admins",
                    "recipient_list_users",
                ],
                "options": [],
            },
            {
                "alerter": "http_request",
                "fields": ["name", "endpoint"],
                "options": ["token_variable_name", "alert_types", "fields", "login_data", "batch_size"],
            },
            {"alerter": "discord", "fields": ["webhook_url", "username"], "options": []},
        ]
        response = self.client.get(reverse("get_alerters"))
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        self.assertEqual(content, expected)

    @mock.patch("impossible_travel.views.alerts.read_config", side_effect=mock_read_config)
    def test_get_active_alerter(self, mock_writer):
        expected = [{"alerter": "discord", "fields": {"webhook_url": "https://discord.com/api/webhooks/WEBHOOK", "username": "BuffaLogs_Alert"}}]
        response = self.client.get(reverse("active_alerter_api"))
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        self.assertEqual(content, expected)

    @mock.patch("impossible_travel.views.alerts.read_config", side_effect=mock_read_config)
    def test_get_alerter_config(self, mock_writer):
        expected = {"alerter": "discord", "fields": {"webhook_url": "https://discord.com/api/webhooks/WEBHOOK", "username": "BuffaLogs_Alert"}}
        response = self.client.get(reverse("alerter_config_api", kwargs={"alerter": "discord"}))
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        self.assertEqual(content, expected)

    @mock.patch("impossible_travel.views.alerts.write_config", side_effect=mock_write_config)
    def test_update_alerter_config(self, mock_writer):
        response = self.client.post(
            f"{reverse('alerter_config_api', kwargs={'alerter' : 'discord'})}",
            json={"webhook_url": "https://my_web_hook_alerter.com"},
            content_type="application/json",
        )
        expected = {"message": "Update successful"}
        self.assertEqual(response.status_code, 200)
        self.assertEqual(expected, json.loads(response.content))
