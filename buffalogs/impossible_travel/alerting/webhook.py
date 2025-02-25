import json
import os
import time
from functools import partial

import jwt
import requests
from django.conf.settings import WEBHOOKS_DEFAULT_ALGORITHM, WEBHOOKS_DEFAULT_ISSUER_ID, WEBHOOKS_DEFAULT_TOKEN_EXPIRATION

from .http_request import HTTPRequestAlerting, Option


class WebHookOption(Option):
    pass


def validate_token_expiration_value(value):
    if not isinstance(value, int):
        raise ValueError(f"{repr(value)} must be an integer.")
    return value


def validate_variable_name(name, allow_empty=True):
    if allow_empty and name == "":
        return name
    if name in os.environ:
        if allow_empty is False and os.environ.get(name, "") == "":
            raise ValueError(f"Environment variable {name} cannot be empty.")
        return name
    raise ValueError(f"{name} must be an environment variable")


WebHookOption.set_default("token_expiration_seconds", WEBHOOKS_DEFAULT_TOKEN_EXPIRATION, parse_func=validate_token_expiration_value)

WebHookOption.set_parser("secret_key_variable_name", partial(validate_variable_name, allow_empty=False))
WebHookOption.set_default("algorithm_variable_name", "", validate_variable_name)
WebHookOption.set_default("issuer_variable_name", "", validate_variable_name)


class WebHookAlerting(HTTPRequestAlerting):
    Option = WebHookOption

    def __init__(self, alert_config: dict):
        super().__init__(alert_config)

    def get_secrets(options: Option):
        s = {}
        s["secret_key"] = os.environs.get(options.secret_key_variable_name)
        s["algorithm"] = os.environs.get(options.algorithm_variable_name, WEBHOOKS_DEFAULT_ALGORITHM)
        s["issuer_id"] = os.environs.get(options.issuer_variable_name, WEBHOOKS_DEFAULT_ISSUER_ID)
        return s

    def generate_jwt(self, recipient_name: str, options: Option):
        """Generate a JWT token with standard claims."""
        current_time = int(time.time())
        webhook_secrets = self.get_secrets(options)

        secret_key = webhook_secrets["secret_key"]
        algorithm = webhook_secrets["algorithm"]
        issuer_id = webhook_secrets["issuer_id"]
        payload = {
            "iss": issuer_id,
            "aud": recipient_name,
            "iat": current_time,
            "exp": current_time + options.token_expiration_seconds,
            "sub": "Alert Notification",
        }
        token = jwt.encode(payload, secret_key, algorithm=algorithm)
        return token

    def send_notification(self, recipient_name: str, endpoint: str, data: dict, options: Option):
        """Send a webhook notification with a JWT Bearer token."""
        token = self.generate_jwt(recipient_name, options)
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        response = requests.post(endpoint, data=data, headers=headers)
        return response
