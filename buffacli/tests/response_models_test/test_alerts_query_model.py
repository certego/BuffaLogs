import unittest

from buffacli.models import AlertQuery


class TestAlertQueryModel(unittest.TestCase):

    def setUp(self):
        # Setup sample input data
        self.sample_data = [
            {
                "timestamp": "2025-03-14T14:16:05.401Z",
                "created": "25-03-14 14:26:12",
                "notified": False,
                "triggered_by": "Amira Booker",
                "rule_name": "New Device",
                "rule_desc": "Login from new device for User: Amira Booker, at: 2025-03-14T14:16:05.401Z",
                "is_vip": False,
                "country": "united states",
                "severity_type": "High",
                "filter_type": [],
            },
            {
                "timestamp": "2025-03-14T14:16:10.790Z",
                "created": "25-03-14 14:26:12",
                "notified": False,
                "triggered_by": "Amira Booker",
                "rule_name": "New Device",
                "rule_desc": "Login from new device for User: Amira Booker, at: 2025-03-14T14:16:10.790Z",
                "is_vip": False,
                "country": "united states",
                "severity_type": "High",
                "filter_type": [],
            },
        ]

        self.alert_query = AlertQuery(self.sample_data, omit=["rule_desc"], mappings={"rule_name": "alert_type"})

    def test_table_format(self):
        expected_table = {
            "alert_type": ["New Device", "New Device"],
            "triggered_by": ["Amira Booker", "Amira Booker"],
            "country": ["united states", "united states"],
            "created": ["25-03-14 14:26:12", "25-03-14 14:26:12"],
            "severity_type": ["High", "High"],
            "is_vip": [False, False],
        }

        # Test the table property
        self.assertEqual(self.alert_query.table, expected_table)

    def test_table_format_multiple_data_response(self):
        # Test table format with multiple entries
        input_data = [
            {
                "timestamp": "2025-03-14T14:16:05.401Z",
                "created": "25-03-14 14:26:12",
                "notified": False,
                "triggered_by": "Amira Booker",
                "rule_name": "New Device",
                "rule_desc": "Login from new device for User: Amira Booker, at: 2025-03-14T14:16:05.401Z",
                "is_vip": False,
                "country": "united states",
                "severity_type": "High",
                "filter_type": [],
            },
            {
                "timestamp": "2025-03-14T14:16:10.790Z",
                "created": "25-03-14 14:26:12",
                "notified": False,
                "triggered_by": "Amira Booker",
                "rule_name": "New Device",
                "rule_desc": "Login from new device for User: Amira Booker, at: 2025-03-14T14:16:10.790Z",
                "is_vip": False,
                "country": "united states",
                "severity_type": "High",
                "filter_type": [],
            },
        ]

        alert_query_multiple = AlertQuery(input_data, omit=["rule_desc"], mappings={"rule_name": "alert_type"})

        expected_table_multiple = {
            "alert_type": ["New Device", "New Device"],
            "triggered_by": ["Amira Booker", "Amira Booker"],
            "country": ["united states", "united states"],
            "created": ["25-03-14 14:26:12", "25-03-14 14:26:12"],
            "severity_type": ["High", "High"],
            "is_vip": [False, False],
        }

        # Test the table property with multiple rows of data
        self.assertEqual(alert_query_multiple.table, expected_table_multiple)

    def test_json_format(self):
        expected_json = [
            {
                "alert_type": "New Device",
                "triggered_by": "Amira Booker",
                "country": "united states",
                "created": "25-03-14 14:26:12",
                "severity_type": "High",
                "is_vip": False,
            },
            {
                "alert_type": "New Device",
                "triggered_by": "Amira Booker",
                "country": "united states",
                "created": "25-03-14 14:26:12",
                "severity_type": "High",
                "is_vip": False,
            },
        ]

        # Test the json property
        self.assertEqual(self.alert_query.json, expected_json)

    def test_json_format_multiple_data_response(self):
        # Test json format with multiple entries
        input_data = [
            {
                "timestamp": "2025-03-14T14:16:05.401Z",
                "created": "25-03-14 14:26:12",
                "notified": False,
                "triggered_by": "Amira Booker",
                "rule_name": "New Device",
                "rule_desc": "Login from new device for User: Amira Booker, at: 2025-03-14T14:16:05.401Z",
                "is_vip": False,
                "country": "united states",
                "severity_type": "High",
                "filter_type": [],
            },
            {
                "timestamp": "2025-03-14T14:16:10.790Z",
                "created": "25-03-14 14:26:12",
                "notified": False,
                "triggered_by": "Amira Booker",
                "rule_name": "New Device",
                "rule_desc": "Login from new device for User: Amira Booker, at: 2025-03-14T14:16:10.790Z",
                "is_vip": False,
                "country": "united states",
                "severity_type": "High",
                "filter_type": [],
            },
        ]

        alert_query_multiple = AlertQuery(input_data, omit=["rule_desc"], mappings={"rule_name": "alert_type"})

        expected_json_multiple = [
            {
                "alert_type": "New Device",
                "triggered_by": "Amira Booker",
                "country": "united states",
                "created": "25-03-14 14:26:12",
                "severity_type": "High",
                "is_vip": False,
            },
            {
                "alert_type": "New Device",
                "triggered_by": "Amira Booker",
                "country": "united states",
                "created": "25-03-14 14:26:12",
                "severity_type": "High",
                "is_vip": False,
            },
        ]

        # Test the json property with multiple rows of data
        self.assertEqual(alert_query_multiple.json, expected_json_multiple)
