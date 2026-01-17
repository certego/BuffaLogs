from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import threading
from unittest import mock

from django.test import TestCase
from impossible_travel.alerting.http_request import (
    PERMITTED_LOGIN_FIELD_LIST,
    HTTPRequestAlerting,
    generate_batch,
)
from impossible_travel.models import Alert, User


def mocked_requests_post_success(endpoint, json, headers):
    "Mock a successful request."

    class MockResponse:
        def __init__(self):
            self.status_code = 200
            self.ok = True
            self.content = "Successful"

    return MockResponse()


def mocked_request_post_failure(endpoint, json, headers):
    "Mock a failed request."

    class MockResponse:
        def __init__(self):
            self.status_code = 400
            self.ok = False
            self.content = "Unsuccessful"

    return MockResponse()


class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Handle POST request by receiving JSON data."""
        content_length = int(self.headers["Content-Length"])
        post_data = self.rfile.read(content_length)
        try:
            json_data = json.loads(post_data)
            self.server.received_data = json_data
        except json.JSONDecodeError:
            self.send_response(400)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Invalid JSON format")
            return

        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"message": "Data received"}).encode())

    def log_message(self, format, *args):
        # do not print out message
        return


def get_test_server():
    """Return server instance."""
    server_address = ("127.0.0.1", 8000)
    try:
        server = HTTPServer(server_address, SimpleHTTPRequestHandler)
    except Exception:
        return None
    server.received_data = None
    return server


def run_test_server(server):
    server.serve_forever()


class TestHTTPRequestAlerting(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_server = get_test_server()
        if cls.test_server:
            cls.server_thread = threading.Thread(target=run_test_server, args=(cls.test_server,), daemon=True)
            cls.server_thread.start()
        super().setUpClass()

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(id=1, username="test_user")

    def setUp(self):
        """Set up the test environment and a sample alerting object"""
        self.config = {}
        self.config["name"] = "test_service"
        self.config["endpoint"] = "http://127.0.0.1:8000"
        self.config["options"] = {}
        self.config["options"]["batch_size"] = 2
        self.config["options"]["fields"] = ["name", "user", "description"]
        self.config["options"]["login_data"] = ["lon", "lat"]
        self.config["options"]["alert_types"] = "_all_"

    def test_configuration_valid(self):
        """Test that configuration works as expected with required fields."""
        alerter = HTTPRequestAlerting(self.config)
        self.assertEqual(alerter.alert_config["name"], "test_service")
        self.assertEqual(alerter.alert_config["endpoint"], "http://127.0.0.1:8000")
        self.assertIn("fields", alerter.alert_config)
        self.assertIn("login_data", alerter.alert_config)
        self.assertIn("token_variable_name", alerter.alert_config)

    def test_configuration_missing_required_fields(self):
        """Test that missing required fields raises an error."""
        invalid_config = self.config.copy()
        del invalid_config["name"]  # Remove required field

        with self.assertRaises(ValueError):
            HTTPRequestAlerting(invalid_config)

    def test_unsupported_field_values_are_dropped(self):
        """
        Test that unsupported or not permitted values for alert_types, fields and login_data are dropped.
        """
        config = self.config.copy()
        config["options"]["fields"] = [
            "user",
            "description",
            "not_permitted_value",
            "created",
            "unsupported_value",
        ]
        config["options"]["login_data"] = "unknown_string_option"
        config["options"]["alert_types"] = "_all_"
        alerter = HTTPRequestAlerting(config)
        fields = alerter.alert_config["fields"]
        login_data = alerter.alert_config["login_data"]
        self.assertEqual(fields, ["user", "description", "created"])
        self.assertEqual(login_data, PERMITTED_LOGIN_FIELD_LIST)

    def test_generate_batch(self):
        """Test that generate_batch correctly groups alerts."""
        alerts = ["alert1", "alert2", "alert3", "alert4", "alert5"]
        batches = list(generate_batch(alerts, 2))
        expected_batches = [["alert1", "alert2"], ["alert3", "alert4"], ["alert5"]]
        self.assertEqual(batches, expected_batches)

        batches = list(generate_batch(alerts, -1))
        expected_batches = alerts[:]
        self.assertEqual(batches, expected_batches)

    def test_serialize_alerts(self):
        """Test that alert serialization works with configured fields."""
        fields = ["name", "user", "description"]
        login_data = ["lat", "lon"]
        alert1 = Alert.objects.create(
            name="New Device",
            user=self.user,
            login_raw_data={"lat": 40.7128, "lon": -74.0060},
            description="test alert",
            notified_status={"http_request": False},
        )

        alert2 = Alert.objects.create(
            name="Imp Travel",
            user=self.user,
            login_raw_data={"lat": 51.5074, "lon": -0.1278},
            description="test alert",
            notified_status={"http_request": False},
        )
        alerter = HTTPRequestAlerting(self.config)
        serialized = alerter.serialize_alerts([alert1, alert2], fields, login_data)
        expected_output = [
            {
                "user": "test_user",
                "name": "New Device",
                "description": "test alert",
                "lat": 40.7128,
                "lon": -74.0060,
            },
            {
                "user": "test_user",
                "name": "Imp Travel",
                "description": "test alert",
                "lat": 51.5074,
                "lon": -0.1278,
            },
        ]

        self.assertTrue(len(expected_output) == len(serialized))
        self.assertTrue(all(expected == data for data, expected in zip(serialized, expected_output)))

    @mock.patch("requests.post", side_effect=mocked_requests_post_success)
    def test_alert_marked_as_notified(self, mock_request):
        """Test that alert are marked as notified."""
        test_endpoint = "http://localhost:5000/alert"

        alert1 = Alert.objects.create(
            name="New Device",
            user=self.user,
            login_raw_data={"lat": 40.7128, "lon": -74.0060},
            description="test alert",
            notified_status={"http_request": False},
        )

        alert2 = Alert.objects.create(
            name="Imp Travel",
            user=self.user,
            login_raw_data={"lat": 51.5074, "lon": -0.1278},
            description="test alert",
            notified_status={"http_request": False},
        )

        alerts = [alert1, alert2]

        alerter = HTTPRequestAlerting(self.config)
        alerter.send_alert("test_service", test_endpoint, alerts)

        alert1 = Alert.objects.get(pk=alert1.pk)
        alert2 = Alert.objects.get(pk=alert2.pk)

        self.assertTrue(alert1.notified_status["http_request"])
        self.assertTrue(alert2.notified_status["http_request"])

    @mock.patch("requests.post", side_effect=mocked_request_post_failure)
    def test_alerts_are_not_marked_as_notified_for_failed_request(self, mock_request):
        test_endpoint = "http://localhost:5000/alert"

        alert1 = Alert.objects.create(
            name="New Device",
            user=self.user,
            login_raw_data={"lat": 40.7128, "lon": -74.0060},
            description="test alert",
            notified_status={"http_request": False},
        )

        alert2 = Alert.objects.create(
            name="Imp Travel",
            user=self.user,
            login_raw_data={"lat": 51.5074, "lon": -0.1278},
            description="test alert",
            notified_status={"http_request": False},
        )

        alerts = [alert1, alert2]

        alerter = HTTPRequestAlerting(self.config)
        alerter.send_alert("test_service", test_endpoint, alerts)

        alert1 = Alert.objects.get(pk=alert1.pk)
        alert2 = Alert.objects.get(pk=alert2.pk)

        self.assertFalse(alert1.notified_status["http_request"])
        self.assertFalse(alert2.notified_status["http_request"])

    def test_notify_with_simple_server(self):
        if self.test_server is None:
            self.skipTest("Failed to create test server")
        alert1 = Alert.objects.create(
            name="New Device",
            user=self.user,
            login_raw_data={"lat": 40.7128, "lon": -74.0060},
            description="test alert",
            notified_status={"http_request": False},
        ).pk

        alert2 = Alert.objects.create(
            name="Imp Travel",
            user=self.user,
            login_raw_data={"lat": 51.5074, "lon": -0.1278},
            description="test alert",
            notified_status={"http_request": False},
        ).pk
        alerter = HTTPRequestAlerting(self.config)
        alerter.notify_alerts()
        expected_data = [
            {
                "name": "New Device",
                "user": "test_user",
                "description": "test alert",
                "lat": 40.7128,
                "lon": -74.0060,
            },
            {
                "name": "Imp Travel",
                "user": "test_user",
                "description": "test alert",
                "lat": 51.5074,
                "lon": -0.1278,
            },
        ]

        received_data = self.test_server.received_data
        self.assertTrue(len(expected_data) == len(received_data))
        self.assertTrue(all(expected == data for data, expected in zip(received_data, expected_data)))

        alert1 = Alert.objects.get(pk=alert1)
        alert2 = Alert.objects.get(pk=alert2)

        self.assertTrue(alert1.notified_status["http_request"])
        self.assertTrue(alert2.notified_status["http_request"])

    @classmethod
    def tearDownClass(cls):
        if cls.test_server is not None:
            try:
                cls.test_server.shutdown()
                cls.test_server.server_close()
            except Exception as e:
                raise ValueError(e)
        super().tearDownClass()
