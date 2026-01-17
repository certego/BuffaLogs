import unittest

from buffacli.models import AlertType


class TestAlertModels(unittest.TestCase):
    def setUp(self):
        self.alert_types_response = [
            {"alert_type": "New Device", "description": "Login from new device"},
            {"alert_type": "Imp Travel", "description": "Impossible Travel detected"},
            {"alert_type": "New Country", "description": "Login from new country"},
            {
                "alert_type": "User Risk Threshold",
                "description": "User risk_score increased",
            },
            {
                "alert_type": "Anonymous IP Login",
                "description": "Login from an anonymous IP",
            },
            {
                "alert_type": "Atypical Country",
                "description": "Login from an atypical country",
            },
        ]

    def test_table_format(self):
        data_model = AlertType(self.alert_types_response, include_description=True)
        expected = {
            "alert_type": [
                "New Device",
                "Imp Travel",
                "New Country",
                "User Risk Threshold",
                "Anonymous IP Login",
                "Atypical Country",
            ],
            "description": [
                "Login from new device",
                "Impossible Travel detected",
                "Login from new country",
                "User risk_score increased",
                "Login from an anonymous IP",
                "Login from an atypical country",
            ],
        }
        self.assertEqual(expected, data_model.table)
        expected.pop("description")
        data_model = AlertType(self.alert_types_response, include_description=False)
        self.assertEqual(expected, data_model.table)
