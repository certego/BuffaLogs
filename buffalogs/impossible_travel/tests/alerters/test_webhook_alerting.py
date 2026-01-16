import json
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import jwt
from django.test import TestCase
from impossible_travel.alerting.webhook import (
    WEBHOOKS_DEFAULT_ALGORITHM,
    WEBHOOKS_DEFAULT_ISSUER_ID,
    WebHookAlerting,
)
from impossible_travel.models import Alert, User

AUDIENCE = "test_service"
SECRET_KEY = "secret_key"
os.environ["TEST_SECRET_KEY"] = SECRET_KEY


class WebhookRequestHandler(BaseHTTPRequestHandler):
    """HTTP server handler that decodes JWT from Authorization header."""

    def do_POST(self):
        """Handle webhook POST request by decoding JWT."""
        auth_header = self.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            self.send_response(401)
            self.end_headers()
            self.wfile.write(b"Unauthorized: Missing or invalid token")
            return

        token = auth_header.split(" ")[1]  # Extract JWT token

        try:
            decoded_token = jwt.decode(
                token,
                SECRET_KEY,
                algorithms=[WEBHOOKS_DEFAULT_ALGORITHM],
                audience=AUDIENCE,
            )
            self.server.decoded_token = decoded_token
        except jwt.ExpiredSignatureError:
            self.send_response(401)
            self.end_headers()
            self.wfile.write(b"Unauthorized: Token has expired")
            return
        except jwt.InvalidTokenError:
            self.send_response(401)
            self.end_headers()
            self.wfile.write(b"Unauthorized: Invalid token")
            return

        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"message": "Webhook received"}).encode())

    def log_message(*args, **kwargs):
        # do not log message
        return


def get_test_server():
    """Return server instance."""
    server_address = ("127.0.0.1", 8000)
    try:
        server = HTTPServer(server_address, WebhookRequestHandler)
    except Exception:
        return None
    server.decoded_token = None
    return server


def run_test_server(server):
    server.serve_forever()


class TestHTTPRequestAlerting(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.test_server = get_test_server()
        if cls.test_server:
            cls.server_thread = threading.Thread(
                target=run_test_server, args=(cls.test_server,), daemon=True
            )
            cls.server_thread.start()
        super().setUpClass()

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(id=1, username="test_user")

    def setUp(self):
        """Set up the test environment and a sample alerting object"""
        self.config = {}
        self.config["name"] = AUDIENCE
        self.config["endpoint"] = "http://127.0.0.1:8000"
        self.config["secret_key_variable_name"] = "TEST_SECRET_KEY"
        self.config["options"] = {}
        self.config["options"]["batch_size"] = 2
        self.config["options"]["fields"] = ["name", "user", "description"]
        self.config["options"]["login_data"] = ["lon", "lat"]
        self.config["options"]["alert_types"] = "_all_"

    def test_configuration_valid(self):
        """Test that configuration works as expected with required fields."""
        alerter = WebHookAlerting(self.config)
        self.assertEqual(alerter.alert_config["name"], AUDIENCE)
        self.assertEqual(alerter.alert_config["endpoint"], "http://127.0.0.1:8000")
        self.assertEqual(
            alerter.alert_config["secret_key_variable_name"], "TEST_SECRET_KEY"
        )
        self.assertIn("fields", alerter.alert_config)
        self.assertIn("login_data", alerter.alert_config)
        self.assertIn("algorithm", alerter.alert_config)
        self.assertIn("issuer", alerter.alert_config)
        self.assertIn("token_expiration_seconds", alerter.alert_config)
        self.assertEqual(WEBHOOKS_DEFAULT_ALGORITHM, alerter.alert_config["algorithm"])
        self.assertEqual(WEBHOOKS_DEFAULT_ISSUER_ID, alerter.alert_config["issuer"])

    def test_configuration_missing_required_fields(self):
        """Test that missing required fields raises an error."""
        invalid_config = self.config.copy()
        del invalid_config["secret_key_variable_name"]  # Remove required field

        with self.assertRaises(ValueError):
            WebHookAlerting(invalid_config)

    def test_notify_with_simple_server(self):
        if self.test_server is None:
            self.skipTest("Failed to create test server")
        alert1 = Alert.objects.create(
            name="New Device",
            user=self.user,
            login_raw_data={"lat": 40.7128, "lon": -74.0060},
            description="test alert",
            notified_status={"webhook": False},
        ).pk

        alert2 = Alert.objects.create(
            name="Imp Travel",
            user=self.user,
            login_raw_data={"lat": 51.5074, "lon": -0.1278},
            description="test alert",
            notified_status={"webhook": False},
        ).pk
        alerter = WebHookAlerting(self.config)
        alerter.notify_alerts()
        alert1 = Alert.objects.get(pk=alert1)
        alert2 = Alert.objects.get(pk=alert2)

    @classmethod
    def tearDownClass(cls):
        if cls.test_server is not None:
            try:
                cls.test_server.shutdown()
                cls.test_server.server_close()
            except Exception as e:
                raise ValueError(e)
        super().tearDownClass()
