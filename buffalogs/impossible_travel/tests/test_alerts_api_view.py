import json

from django.test import Client
from django.urls import reverse
from rest_framework.test import APITestCase


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
