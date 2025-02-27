import time

import jwt
import requests
from django.conf.settings import WEBHOOKS_DEFAULT_ALGORITHM, WEBHOOKS_DEFAULT_ISSUER_ID, WEBHOOKS_DEFAULT_TOKEN_EXPIRATION

from .http_request import HTTPRequestAlerting


def validate_token_expiration_value(value):
    if not isinstance(value, int):
        return f"{repr(value)} must be an integer.", WEBHOOKS_DEFAULT_TOKEN_EXPIRATION
    return None, value


class WebHookAlerting(HTTPRequestAlerting):

    option_parsers = {"token_expiration_seconds": validate_token_expiration_value}
    required_fields = ["name", "endpoint", "secret_key_variable_name"]

    def generate_jwt(self):
        """Generate a JWT token with standard claims."""
        current_time = int(time.time())
        token_expiration_seconds = self.alert_config["token_expiration_seconds"]
        secret_key = self.alert_config["secret_key"]
        algorithm = self.alert_config["algorithm"]
        issuer_id = self.alert_config["issuer_id"]
        recipient_name = self.alert_config["name"]
        payload = {
            "iss": issuer_id,
            "aud": recipient_name,
            "iat": current_time,
            "exp": current_time + token_expiration_seconds,
            "sub": "Alert Notification",
        }
        token = jwt.encode(payload, secret_key, algorithm=algorithm)
        return token

    def send_notification(self, recipient_name: str, endpoint: str, data: dict):
        """Send a webhook notification with a JWT Bearer token."""
        token = self.generate_jwt()
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        response = requests.post(endpoint, data=data, headers=headers)
        return response
