import os
import time

import jwt

try:
    import requests
except ImportError:
    pass
from .http_request import HTTPRequestAlerting

WEBHOOKS_ALGORITHM_LIST = jwt.algorithms.get_default_algorithms()
WEBHOOKS_DEFAULT_ALGORITHM = "HS256"
WEBHOOKS_DEFAULT_ISSUER_ID = "buffalogs_webhook"
WEBHOOKS_DEFAULT_TOKEN_EXPIRATION = 60 * 5  # Token expiration time in seconds (5 minutes)


def validate_token_expiration_value(value: int):
    """Check that value is an int object."""
    if not isinstance(value, int):
        return f"{repr(value)} must be an integer.", WEBHOOKS_DEFAULT_TOKEN_EXPIRATION
    return None, value


def parse_hash_algorithm(value: str):
    """Check that value is one of the supported webhooks algorithms."""
    if value in WEBHOOKS_ALGORITHM_LIST:
        return "", value
    return f"Algorithm option {value} is not supported", WEBHOOKS_DEFAULT_ALGORITHM


class WebHookAlerting(HTTPRequestAlerting):

    required_fields = ["name", "endpoint", "secret_key_variable_name"]
    extra_option_parsers = {
        "token_expiration_seconds": validate_token_expiration_value,
        "algorithm": parse_hash_algorithm,
    }
    extra_options = {
        "token_expiration_seconds": WEBHOOKS_DEFAULT_TOKEN_EXPIRATION,
        "algorithm": WEBHOOKS_DEFAULT_ALGORITHM,
        "issuer": WEBHOOKS_DEFAULT_ISSUER_ID,
    }

    def get_secret_key(self, key_name: str):
        """
        Get secret_key.

        key_name : Environment variable name storing secret key.
        """
        return os.environ[key_name]

    def generate_jwt(self):
        """Generate a JWT token with standard claims."""
        current_time = int(time.time())
        token_expiration_seconds = self.alert_config["token_expiration_seconds"]
        secret_key_name = self.alert_config["secret_key_variable_name"]
        secret_key = self.get_secret_key(secret_key_name)
        algorithm = self.alert_config["algorithm"]
        issuer_id = self.alert_config["issuer"]
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
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        response = requests.post(endpoint, json=data, headers=headers)
        return response
