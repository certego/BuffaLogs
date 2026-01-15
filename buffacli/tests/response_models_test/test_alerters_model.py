import unittest

from buffacli.models import Alerters


class TestAlertModels(unittest.TestCase):

    def setUp(self):
        self.alerter_list_response = [
            {"alerter": "slack", "fields": ["webhook_url"], "options": []},
            {"alerter": "telegram", "fields": ["bot_token", "chat_ids"], "options": []},
        ]

        self.alerter_response = {
            "alerter": "telegram",
            "fields": {"bot_token": "BOT_TOKEN", "chat_ids": ["CHAT_ID"]},
        }

    def test_table_format_for_alerters_list(self):
        data_model = Alerters(self.alerter_list_response)
        expected = {
            "alerter": ["slack", "telegram"],
            "fields": ["webhook_url", "bot_token, chat_ids"],
        }
        self.assertEqual(expected, data_model.table)

    def test_table_format_for_single_alerter(self):
        data_model = Alerters(self.alerter_response)
        expected = {"fields": ["bot_token", "chat_ids"], "": ["BOT_TOKEN", ["CHAT_ID"]]}
        self.assertEqual(expected, data_model.table)
